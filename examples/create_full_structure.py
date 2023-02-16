from indico_toolkit import create_client
from indico_toolkit.structure.create_structure import Structure

"""
Creating a full Indico Workflow from dataset, workflow, and model creation
"""

HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"

client = create_client(HOST, API_TOKEN_PATH)
structure = Structure(client)

optional_ocr_options = {
    "auto_rotate": False,
    "upscale_images": True,
    "languages": ["ENG"],
}

# creates dataset
# optional kwargs single_column
dataset = structure.create_dataset(
    dataset_name="Dataset Name",
    files_to_upload=["./path_to_file"],
    read_api=True,
    single_column=False,
    **optional_ocr_options
)

# creates workflow
# optionaly provide dataset id. If not, inferred from structure.dataset.id
workflow = structure.create_workflow("Workflow Name", dataset.id)

# creates extraction model
# optional kwarg for advanced training options: auto_negative_scaling=False
structure.add_teach_task(
    task_name="Teach Task Name",
    labelset_name="Extraction Labelset",
    target_names=["Label 1", "Label2"],
    dataset_id=dataset.id,
    workflow_id=workflow.id,
    model_type="annotation",
    auto_negative_scaling=False,
)
