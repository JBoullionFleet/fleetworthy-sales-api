import os
import logging
from typing import List, Dict, Any
import PyPDF2
import chromadb
from sentence_transformers import SentenceTransformer
import openai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class FleetworthyKnowledgeBase:
    """
    RAG system for Fleetworthy sales materials and company information
    """
    
    def __init__(self, knowledge_dir: str = "./fleetworthy_docs"):
        self.knowledge_dir = knowledge_dir
        self.chroma_client = None
        self.collection = None
        self.embedding_model = None
        self.openai_client = None
        
        # Create directories
        os.makedirs(knowledge_dir, exist_ok=True)
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize ChromaDB, embedding model, and OpenAI client"""
        try:
            # Initialize ChromaDB
            self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
            self.collection = self.chroma_client.get_or_create_collection(
                name="fleetworthy_knowledge",
                metadata={"description": "Fleetworthy sales materials and company information"}
            )
            
            # Initialize embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize OpenAI client
            if os.getenv("OPENAI_API_KEY"):
                self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            logger.info("✅ Knowledge base components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing knowledge base: {e}")
            raise
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from a PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                
                return text.strip()
                
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks for better retrieval"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
    
    def add_document(self, file_path: str, document_type: str = "sales_material") -> bool:
        """Add a PDF document to the knowledge base"""
        try:
            # Extract text from PDF
            text = self.extract_text_from_pdf(file_path)
            if not text:
                logger.warning(f"No text extracted from {file_path}")
                return False
            
            # Chunk the text
            chunks = self.chunk_text(text)
            
            # Generate embeddings and store in ChromaDB
            for i, chunk in enumerate(chunks):
                chunk_id = f"{os.path.basename(file_path)}_chunk_{i}"
                
                # Generate embedding
                embedding = self.embedding_model.encode(chunk).tolist()
                
                # Store in ChromaDB
                self.collection.add(
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        "source": os.path.basename(file_path),
                        "document_type": document_type,
                        "chunk_index": i
                    }],
                    ids=[chunk_id]
                )
            
            logger.info(f"✅ Added {len(chunks)} chunks from {file_path} to knowledge base")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document {file_path}: {e}")
            return False
    
    def search_knowledge(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base for relevant information"""
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "content": results['documents'][0][i],
                    "source": results['metadatas'][0][i]['source'],
                    "document_type": results['metadatas'][0][i]['document_type'],
                    "relevance_score": 1 - results['distances'][0][i]  # Convert distance to similarity
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def get_relevant_context(self, query: str, max_context_length: int = 2000) -> str:
        """Get relevant context from knowledge base for a query"""
        results = self.search_knowledge(query, n_results=5)
        
        if not results:
            return ""
        
        # Combine relevant chunks
        context_parts = []
        current_length = 0
        
        for result in results:
            content = result['content']
            if current_length + len(content) <= max_context_length:
                context_parts.append(f"From {result['source']}: {content}")
                current_length += len(content)
            else:
                break
        
        return "\n\n".join(context_parts)
    
    def process_uploaded_pdfs(self):
        """Process all PDFs in the knowledge directory"""
        processed_count = 0
        
        for filename in os.listdir(self.knowledge_dir):
            if filename.lower().endswith('.pdf'):
                file_path = os.path.join(self.knowledge_dir, filename)
                if self.add_document(file_path, "sales_material"):
                    processed_count += 1
        
        logger.info(f"✅ Processed {processed_count} PDF documents")
        return processed_count
    
    def generate_enhanced_response(self, question: str, web_research: str = "") -> str:
        """Generate a response enhanced with knowledge base information"""
        if not self.openai_client:
            logger.warning("OpenAI client not available, returning web research only")
            return web_research
        
        try:
            # Get relevant context from knowledge base
            kb_context = self.get_relevant_context(question)
            
            # Create enhanced prompt
            system_prompt = """You are a friendly Fleetworthy sales agent. Use the provided company knowledge and web research to give helpful, conversational responses about Fleetworthy's services.

Keep responses to 2-4 sentences and focus on specific benefits that match the customer's needs."""
            
            user_prompt = f"""Question: {question}

Fleetworthy Company Knowledge:
{kb_context}

Web Research Context:
{web_research}

Please provide a helpful, conversational response about how Fleetworthy can help."""
            
            # Generate response using OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating enhanced response: {e}")
            return web_research
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "status": "ready" if count > 0 else "empty"
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"total_chunks": 0, "status": "error"}

# Global instance
knowledge_base = FleetworthyKnowledgeBase()

def initialize_knowledge_base():
    """Initialize and populate the knowledge base"""
    try:
        # Process any existing PDFs
        count = knowledge_base.process_uploaded_pdfs()
        stats = knowledge_base.get_stats()
        
        logger.info(f"Knowledge base initialized: {stats}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize knowledge base: {e}")
        return False