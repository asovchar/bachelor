"""Create aggregation function

Revision ID: ebf43a9c712b
Revises: d4c028ee7223
Create Date: 2020-05-31 12:04:45.024497

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ebf43a9c712b'
down_revision = 'd4c028ee7223'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            CREATE OR REPLACE FUNCTION vec_add(arr1 double precision[], arr2 double precision[])
            RETURNS double precision[] AS
            $$
            SELECT array_agg(result)
            FROM (SELECT coalesce(tuple.val1, 0) + coalesce(tuple.val2, 0) AS result
                  FROM (SELECT UNNEST($1) AS val1,
                               UNNEST($2) AS val2,
                               generate_subscripts($1, 1) AS ix) tuple
                  ORDER BY ix) inn;
            $$ LANGUAGE SQL IMMUTABLE STRICT;
            
            CREATE AGGREGATE vec_sum(double precision[]) (
                SFUNC = vec_add,
                STYPE = double precision[]
            );
        """)
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            DROP AGGREGATE vec_sum(double precision[]);
            DROP FUNCTION vec_add(arr1 double precision[], arr2 double precision[]);
        """)
    )
