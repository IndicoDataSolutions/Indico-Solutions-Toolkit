from indico.queries import GraphQLRequest

class GetDatasetDetails(GraphQLRequest):
    GET_DATASET_DETAILS = """
        query getDataset($id: Int!) {
            dataset(id: $id) {
                id
                name
                rowCount
                status
                createdAt
                updatedAt
                datacolumns {
                    id
                    name
                }
                labelsets{
                    id
                    name
                }
                files {
                    id
                    deleted
                    name
                    status
                    statusMeta
                    fileSize
                    fileType
                    numPages
                }
            }
        }
    """

    def __init__(self, *, dataset_id: int):
        super().__init__(
            self.GET_DATASET_DETAILS,
            variables={"id": dataset_id},
        )

    def process_response(self, response):
        return super().process_response(response)