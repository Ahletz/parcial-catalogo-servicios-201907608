class CatalogImportError(Exception):
    """Error fatal de importación; puede referenciar una ejecución persistida."""

    def __init__(self, message, execution_id=None):
        super().__init__(message)
        self.execution_id = execution_id
