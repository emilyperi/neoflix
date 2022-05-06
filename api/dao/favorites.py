from api.data import popular, goodfellas
from api.exceptions.notfound import NotFoundException

class FavoriteDAO:
    """
    The constructor expects an instance of the Neo4j Driver, which will be
    used to interact with Neo4j.
    """
    def __init__(self, driver):
        self.driver=driver


    """
    This method should retrieve a list of movies that have an incoming :HAS_FAVORITE
    relationship from a User node with the supplied `userId`.

    Results should be ordered by the `sort` parameter, and in the direction specified
    in the `order` parameter.

    Results should be limited to the number passed as `limit`.
    The `skip` variable should be used to skip a certain number of rows.
    """
    # tag::all[]
    def all(self, user_id, sort = 'title', order = 'ASC', limit = 6, skip = 0):
        def get_favorites(tx, user_id, sort, order, limit, skip):
            cypher = """
                    MATCH (u:User {{userId: $user_id}})-[r:HAS_FAVORITE]->(m:Movie)
                    RETURN m {{
                            .*,
                            favorite: true
                            }} AS movie
                    ORDER BY m.`{0}` {1}
                    SKIP $skip
                    LIMIT $limit
                    """.format(sort, order)
            result = tx.run(cypher, user_id=user_id, limit=limit, skip=skip)
            return [row.value("movie") for row in result]
        
        with self.driver.session() as session:
            favorites = session.read_transaction(get_favorites, user_id=user_id, sort=sort, order=order, limit=limit, skip=skip)
        return favorites
    # end::all[]


    """
    This method should create a `:HAS_FAVORITE` relationship between
    the User and Movie ID nodes provided.
   *
    If either the user or movie cannot be found, a `NotFoundError` should be thrown.
    """
    # tag::add[]
    def add(self, user_id, movie_id):
        def create_favorite(tx, user_id, movie_id):
            cypher = """
                    MATCH (u:User {userId: $user_id})
                    MATCH (m:Movie {tmdbId: $movie_id})
                    MERGE (u)-[f:HAS_FAVORITE]->(m)
                    ON CREATE SET u.createdAt = datetime()
                    RETURN m {
                        .*,
                        favorite: true
                        } AS movie
                    """
            return tx.run(cypher, user_id=user_id, movie_id=movie_id).single()
        
        with self.driver.session() as session:
            record = session.write_transaction(create_favorite, user_id=user_id, movie_id=movie_id)

        if record is None:
            raise NotFoundException

        return record.get("movie")
    # end::add[]

    """
    This method should remove the `:HAS_FAVORITE` relationship between
    the User and Movie ID nodes provided.

    If either the user, movie or the relationship between them cannot be found,
    a `NotFoundError` should be thrown.
    """
    # tag::remove[]
    def remove(self, user_id, movie_id):
        def delete_favorite(tx, user_id, movie_id):
            cypher = """
                    MATCH (u:User {userId: $user_id})-[r:HAS_FAVORITE]->(m:Movie {tmdbId: $movie_id})
                    DELETE r
                    RETURN m {
                            .*,
                            favorite: false
                         } AS movie
                    """
            return tx.run(cypher, user_id=user_id, movie_id=movie_id).single()
        
        with self.driver.session() as session:
            record = session.write_transaction(delete_favorite, user_id=user_id, movie_id=movie_id)

        if record is None:
            raise NotFoundException

        return record.get("movie")
    # end::remove[]
