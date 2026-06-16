import pytest
from unittest.mock import MagicMock, patch
from src.evals import create_eval_dataset, run_faithfulness_eval

class MockFeedback:
    def __init__(self, key, score):
        self.key = key
        self.score = score

class MockRunResult:
    def __init__(self, key, score):
        self.feedback = [MockFeedback(key, score)]

@patch("src.evals.Client")
def test_create_eval_dataset_new(mock_client_cls):
    mock_client = MagicMock()
    mock_client.has_dataset.return_value = False
    
    mock_dataset = MagicMock()
    mock_dataset.id = "mock-id"
    mock_client.create_dataset.return_value = mock_dataset
    mock_client_cls.return_value = mock_client
    
    create_eval_dataset("test-dataset")
    
    mock_client.has_dataset.assert_called_once_with(dataset_name="test-dataset")
    mock_client.create_dataset.assert_called_once()
    assert mock_client.create_example.call_count == 5

@patch("src.evals.Client")
def test_create_eval_dataset_exists(mock_client_cls):
    mock_client = MagicMock()
    mock_client.has_dataset.return_value = True
    mock_client_cls.return_value = mock_client
    
    create_eval_dataset("test-dataset")
    
    mock_client.has_dataset.assert_called_once_with(dataset_name="test-dataset")
    mock_client.create_dataset.assert_not_called()
    mock_client.create_example.assert_not_called()

@patch("src.evals.evaluate")
@patch("src.evals.get_faithfulness_evaluator")
@patch("src.evals.create_eval_dataset")
def test_run_faithfulness_eval_success(mock_create, mock_get_evaluator, mock_evaluate):
    # Mock evaluate results
    mock_results = [
        MockRunResult("faithfulness", 1.0),
        MockRunResult("faithfulness", 0.90)
    ]
    mock_evaluate.return_value = mock_results
    
    # Mock evaluator
    mock_evaluator = MagicMock()
    mock_get_evaluator.return_value = mock_evaluator
    
    avg_score = run_faithfulness_eval("test-dataset")
    
    assert avg_score == 0.95
    mock_create.assert_called_once_with("test-dataset")
    mock_evaluate.assert_called_once()

@patch("src.evals.evaluate")
@patch("src.evals.get_faithfulness_evaluator")
@patch("src.evals.create_eval_dataset")
def test_run_faithfulness_eval_failure(mock_create, mock_get_evaluator, mock_evaluate):
    # Mock evaluate results below threshold
    mock_results = [
        MockRunResult("faithfulness", 0.80),
        MockRunResult("faithfulness", 0.70)
    ]
    mock_evaluate.return_value = mock_results
    
    # Mock evaluator
    mock_evaluator = MagicMock()
    mock_get_evaluator.return_value = mock_evaluator
    
    with pytest.raises(ValueError, match="is below the required threshold of 0.85"):
        run_faithfulness_eval("test-dataset")
