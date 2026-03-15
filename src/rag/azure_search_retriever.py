"""
Azure AI Search Retriever Module
Implement production-grade retrieval from Azure AI Search with Hybrid and Vector Search capabilities.
Developed for Enterprise GenAI Orchestrator.
"""

from typing import List, Dict, Any, Optional
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI
from loguru import logger

class AzureSearchRetriever:
    """
    A professional-grade retriever using Azure AI Search (formerly Cognitive Search)
    and Azure OpenAI for embeddings.
    """

    def __init__(
        self,
        endpoint: str,
        index_name: str,
        api_key: str,
        aoai_endpoint: str,
        aoai_api_key: str,
        aoai_embedding_deployment: str,
    ):
        """
        Initializes the retriever with necessary Azure resource credentials.
        """
        self.search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(api_key),
        )
        self.aoai_client = AzureOpenAI(
            azure_endpoint=aoai_endpoint,
            api_key=aoai_api_key,
            api_version="2023-05-15",
        )
        self.embedding_deployment = aoai_embedding_deployment
        logger.info(f"Initialized AzureSearchRetriever for index: {index_name}")

    def get_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings for a given query text using Azure OpenAI.
        """
        try:
            response = self.aoai_client.embeddings.create(
                input=[text], model=self.embedding_deployment
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

    def search(
        self, 
        query: str, 
        top_k: int = 5, 
        use_vector_search: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform a hybrid or vector-only search on Azure AI Search.
        """
        logger.debug(f"Searching for: {query}")
        
        search_kwargs: Dict[str, Any] = {
            "search_text": query,
            "top": top_k,
        }

        if use_vector_search:
            vector_query = VectorizedQuery(
                vector=self.get_embeddings(query),
                k_nearest_neighbors=top_k,
                fields="content_vector",
            )
            search_kwargs["vector_queries"] = [vector_query]

        results = self.search_client.search(**search_kwargs)
        
        retrieved_docs = []
        for result in results:
            retrieved_docs.append({
                "id": result.get("id"),
                "content": result.get("content"),
                "score": result.get("@search.score"),
                "metadata": result.get("metadata", {}),
            })
            
        logger.info(f"Retrieved {len(retrieved_docs)} documents for query: {query}")
        return retrieved_docs

if __name__ == "__main__":
    # Example usage / Quick test
    # Configure via env vars or manual entry
    pass
