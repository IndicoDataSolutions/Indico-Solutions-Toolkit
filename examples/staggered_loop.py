"""
Convert human reviewed submissions from a workflow to a 'labeled data'format and writes it to CSV.
"""
from indico_toolkit.staggered_loop import StaggeredLoop
from indico_toolkit import create_client


client = create_client("app.indico.io", "./indico_api_token.txt")
stagger = StaggeredLoop(client)
# workflow_id is required, but optionally specify submission ids to include and 
# the specific model name if more than 1 in workflow
stagger.get_reviewed_prediction_data(
    workflow_id=412, submission_ids=[123, 415, 987], model_name="model_v1"
)
stagger.write_csv("./data_to_add_to_model.csv")
