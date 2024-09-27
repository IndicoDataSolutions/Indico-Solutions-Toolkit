from indico_toolkit import results


def test_empy_v1_sections() -> None:
    result = results.load(
        """
        {
            "file_version": 1,
            "submission_id": 0,
            "etl_output": "",
            "results": {
                "document": {
                    "results": {
                        "Empty Model Section": []
                    }
                }
            }
        }
        """
    )
    assert result.predictions.to_changes(result) == {
        "Empty Model Section": [],
    }


def test_empy_v3_sections() -> None:
    result = results.load(
        """
        {
            "file_version": 3,
            "submission_id": 0,
            "modelgroup_metadata": {
                "123": {
                    "id": 123,
                    "task_type": "annotation",
                    "name": "Empty Model Section",
                    "selected_model": {
                        "id": 123,
                        "model_type": "finetune"
                    }
                }
            },
            "submission_results": [
                {
                    "submissionfile_id": 0,
                    "etl_output": "",
                    "input_filename": "",
                    "model_results": {
                        "ORIGINAL": {
                            "123": []
                        }
                    }
                }
            ]
        }
        """
    )
    assert result.predictions.to_changes(result) == [
        {
            "submissionfile_id": 0,
            "model_results": {
                "123": [],
            },
            "component_results": {},
        }
    ]
