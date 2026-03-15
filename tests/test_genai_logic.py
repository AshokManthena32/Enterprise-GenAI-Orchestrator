"""
Pytest Suite for GenAI Logic
Validates the RAG retriever and autonomous agent reasoning.
"""

import pytest
from unittest.mock import MagicMock, patch
from src.rag.azure_search_retriever import AzureSearchRetriever
from src.agents.autonomous_agent import AutonomousAgent, get_company_revenue

# --- Mocking Strategy ---

@pytest.fixture
def mock_aoai_client():
    with patch("src.rag.azure_search_retriever.AzureOpenAI") as mock:
        client_instance = mock.return_value
        # Mock embedding response
        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.1, 0.2, 0.3]
        client_instance.embeddings.create.return_value.data = [mock_embedding]
        yield client_instance

@pytest.fixture
def mock_search_client():
    with patch("src.rag.azure_search_retriever.SearchClient") as mock:
        client_instance = mock.return_value
        # Mock search results
        mock_result = {
            "id": "1",
            "content": "Azure AI Search is an enterprise search service.",
            "@search.score": 1.0,
            "metadata": {"source": "documentation"}
        }
        client_instance.search.return_value = [mock_result]
        yield client_instance

# --- Retriever Tests ---

def test_retriever_search_logic(mock_search_client, mock_aoai_client):
    """
    Test that the retriever correctly processes queries and interacts with Azure services.
    """
    retriever = AzureSearchRetriever(
        endpoint="https://mock-search.net",
        index_name="test-index",
        api_key="mock-key",
        aoai_endpoint="https://mock-aoai.net",
        aoai_api_key="mock-aoai-key",
        aoai_embedding_deployment="text-emb-3"
    )
    
    results = retriever.search("What is AI Search?")
    
    assert len(results) == 1
    assert results[0]["id"] == "1"
    assert "enterprise search service" in results[0]["content"]
    assert mock_aoai_client.embeddings.create.called
    assert mock_search_client.search.called

# --- Agent Tests ---

def test_tool_logic():
    """Test the mock tool directly."""
    result = get_company_revenue("MSFT")
    assert "$15.4B" in result

@pytest.mark.asyncio
async def test_agent_run_mock():
    """
    Test the agent execution flow (mocked).
    """
    with patch("src.agents.autonomous_agent.AgentExecutor.ainvoke") as mock_ainvoke:
        mock_ainvoke.return_value = {"output": "Mocked AI Response"}
        
        agent = AutonomousAgent(
            azure_endpoint="https://mock.openai.com",
            api_key="mock-key",
            api_version="2023-05-15",
            deployment_name="gpt-4o"
        )
        
        response = await agent.run("Hello world")
        assert response == "Mocked AI Response"
        assert mock_ainvoke.called
