from huggingface_hub import logging
import os 
import glob 
import logging 
from dotenv import load_dotenv

load_dotenv(override=True)

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import AzureSearch

from langchain_huggingface import HuggingFaceEmbeddings

logging.basicConfig(
    level=logging.INFO ,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger()

def index_docs():
    '''
    Reads the pdf, chunks them , and upload them to Azure AI Search
    '''
    try:
        # Fixed path resolution
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_folder= os.path.join(current_dir, "../data")

        logger.info(f"Looking for PDFs in: {data_folder}")

        embeddings = HuggingFaceEmbeddings(
          model_name=os.getenv("EMBEDDING_MODEL", 'sentence-transformers/all-MiniLM-L6-v2')
        )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(os.getenv("CHUNK_SIZE", 1000)),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", 200)),
            separators=["\n\n", "\n", ".", " "],
        )

        pdf_path=os.path.join(data_folder, "*.pdf")
        all_splits=[]

        for file in glob.glob(pdf_path):
            logger.info(f"Processing {os.path.basename(file)}")

            loader = PyPDFLoader(file)
            pages = loader.load()
            doc = splitter.split_documents(pages)

            logger.info(f"Split {os.path.basename(file)} into {len(doc)} chunks")

            # Fixed metadata source to use current file's basename
            for idx, chunk in enumerate(doc):
                chunk.metadata["source"]=os.path.basename(file)
            
            # Fixed extend to use doc instead of chunk
            all_splits.extend(doc)

        if all_splits:
            logger.info(f"Connecting to Azure AI Search... (Total chunks to upload: {len(all_splits)})")
            
            # Move vector store initialization outside the loop so we only do it once
            vector_store = AzureSearch(
                azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
                azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
                index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
                embedding_function=embeddings.embed_query
            )

            logger.info("Uploading documents to Azure AI Search. This may take a moment...")
            vector_store.add_documents(documents=all_splits)
            logger.info("Successfully uploaded all documents to the vector store!")
        else:
            logger.warning("No PDF files found or no chunks were generated. Skipping upload.")
            
    except Exception as e:
        logger.error(f"An error occurred while indexing documents: {e}", exc_info=True)

if __name__ == "__main__":
    index_docs()