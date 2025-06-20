# app.py - Enhanced Flask backend with MCP web search integration

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
from datetime import datetime
import base64
import asyncio

# Import our research agent
from agents.research_agent import create_research_agent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Enable CORS for all origins (restrict in production)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}

# Create upload directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_fleetworthy_related(question: str) -> bool:
    """
    Check if a question is related to Fleetworthy services
    This is a simple keyword-based check that can be enhanced later
    """
    fleetworthy_keywords = [
        'fleet', 'truck', 'trucking', 'transportation', 'logistics', 'delivery',
        'route', 'fuel', 'driver', 'vehicle', 'dispatch', 'maintenance',
        'tracking', 'gps', 'shipping', 'cargo', 'freight', 'load',
        'fleetworthy', 'cost', 'efficiency', 'optimization', 'management',
        'safety', 'compliance', 'eld', 'hours of service', 'dot'
    ]
    
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in fleetworthy_keywords)

def generate_ai_response_sync(question: str, company_website: str = "", 
                             company_description: str = "", file_info: dict = None) -> str:
    """
    Synchronous wrapper for the async AI response generation
    """
    # Create a new event loop for this thread
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Run the async function
    return loop.run_until_complete(
        generate_ai_response_async(question, company_website, company_description, file_info)
    )

async def generate_ai_response_async(question: str, company_website: str = "", 
                             company_description: str = "", file_info: dict = None) -> str:
    """
    Generate AI response using research agent
    """
    try:
        # Check if question is Fleetworthy-related
        if not is_fleetworthy_related(question):
            return "Sorry, but I can only help with questions about Fleetworthy's fleet management solutions. Please ask me about our transportation, logistics, or fleet management services!"
        
        # Create research agent (uses session-based memory)
        session_id = "main"  # In production, use user-specific session IDs
        research_agent = create_research_agent(session_id)
        
        # Prepare context for the research agent
        context = {
            'company_website': company_website,
            'company_description': company_description,
            'file_info': file_info
        }
        
        # If we have company information, do company research
        if company_website or company_description:
            logger.info(f"Researching company: {company_website}")
            company_research = await research_agent.research_company(
                company_website, company_description
            )
            
            # Now research the specific question with company context
            question_research = await research_agent.research_question(question, context)
            
            # Combine the insights
            response = f"{question_research}\n\n---\n\n**Additional Company Insights:**\n{company_research}"
            
        else:
            # Just research the question without company context
            response = await research_agent.research_question(question, context)
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        return "I apologize, but I encountered an error while researching your question. Please try again, and if the issue persists, feel free to contact our sales team directly."

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "message": "Fleetworthy Sales Agent API is running!",
        "timestamp": datetime.now().isoformat(),
        "status": "healthy"
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint that receives all frontend data
    Expected JSON payload:
    {
        "question": "User's question",
        "company_website": "https://example.com",
        "company_description": "About the company",
        "file_data": "base64_encoded_file_data",
        "file_name": "document.pdf",
        "file_type": "application/pdf"
    }
    """
    try:
        # Log the incoming request
        logger.info(f"Received chat request from {request.remote_addr}")
        
        # Check if request contains JSON
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        logger.info(f"Request data keys: {list(data.keys())}")

        # Extract and validate required fields
        question = data.get('question', '').strip()
        if not question:
            return jsonify({"error": "Question is required"}), 400

        # Extract optional fields
        company_website = data.get('company_website', '').strip()
        company_description = data.get('company_description', '').strip()
        file_data = data.get('file_data')
        file_name = data.get('file_name')
        file_type = data.get('file_type')

        # Validate URL if provided
        if company_website and not validate_url(company_website):
            return jsonify({"error": "Invalid website URL format"}), 400

        # Process file if provided
        file_info = None
        if file_data and file_name:
            try:
                # Validate file type
                if not allowed_file(file_name):
                    return jsonify({"error": f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
                
                # Decode base64 file data
                file_content = base64.b64decode(file_data)
                file_size = len(file_content)
                
                # Check file size
                if file_size > app.config['MAX_CONTENT_LENGTH']:
                    return jsonify({"error": "File too large. Maximum size is 5MB"}), 400
                
                # Save file (for testing purposes)
                file_path = os.path.join(UPLOAD_FOLDER, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}")
                with open(file_path, 'wb') as f:
                    f.write(file_content)
                
                file_info = {
                    "name": file_name,
                    "type": file_type,
                    "size": file_size,
                    "saved_path": file_path
                }
                logger.info(f"File saved: {file_name} ({file_size} bytes)")
                
            except Exception as e:
                logger.error(f"File processing error: {str(e)}")
                return jsonify({"error": "Error processing uploaded file"}), 400

        # Log all received data (for testing)
        logger.info("=== RECEIVED DATA ===")
        logger.info(f"Question: {question}")
        logger.info(f"Company Website: {company_website}")
        logger.info(f"Company Description: {company_description[:100]}..." if len(company_description) > 100 else company_description)
        logger.info(f"File Info: {file_info}")
        logger.info("===================")

        # Generate AI response using research agent
        logger.info("Generating AI response...")
        ai_response = generate_ai_response_sync(
            question=question,
            company_website=company_website,
            company_description=company_description,
            file_info=file_info
        )

        return jsonify({
            "message": ai_response,
            "received_data": {
                "question": question,
                "has_website": bool(company_website),
                "has_description": bool(company_description),
                "has_file": bool(file_info),
                "file_info": file_info
            },
            "timestamp": datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/hello', methods=['POST'])
def hello_world():
    """
    Legacy endpoint for backward compatibility
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    name = data.get('name')

    if name:
        response_message = f"Hello, {name}! Welcome to the Fleetworthy Sales Portal."
        return jsonify({"message": response_message}), 200
    else:
        return jsonify({"error": "Name field is required"}), 400

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify API is working"""
    return jsonify({
        "status": "API is working!",
        "timestamp": datetime.now().isoformat(),
        "upload_folder": UPLOAD_FOLDER,
        "max_file_size": app.config['MAX_CONTENT_LENGTH'],
        "allowed_extensions": list(ALLOWED_EXTENSIONS)
    })

def validate_url(url):
    """Basic URL validation"""
    if not url:
        return True  # Optional field
    return url.startswith(('http://', 'https://'))

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({"error": "File too large. Maximum size is 5MB"}), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Development server
    logger.info("Starting Fleetworthy Sales API in development mode...")
    app.run(debug=True, host='0.0.0.0', port=5000)