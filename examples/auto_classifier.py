"""
Create a CSV that can be used to train a model without any labeling using an organized 
directory/folder structure. 

e.g. you would target '/base_directory/' if you had your files organized like:

/base_directory/invoices/ -> contains all invoices
/base_directory/disclosures/ -> contains all disclosures

"""
from indico_toolkit.auto_class import AutoClassifier
from indico_toolkit import create_client

HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"
PATH_TO_DIR = "./base_directory/"

# Instantiate the FindRelated class
client = create_client(HOST, API_TOKEN_PATH)

autoclass = AutoClassifier(client, PATH_TO_DIR)
autoclass.set_file_paths(accepted_types=("pdf", "tiff"))
autoclass.create_classifier(verbose=True, batch_size=5)
autoclass.to_csv("./auto_classifier.csv")
