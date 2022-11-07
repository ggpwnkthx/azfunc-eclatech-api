from ..base import Abstract as ABT
#Location table
class Demo(ABT):
    """
    Demo model for database tables
    """
        
    JSONAPI = {
        "methods": ['GET','POST','DELETE','PATCH'],
        "allow_to_many_replacement": True,
        "allow_delete_from_to_many_relationships": True
    }