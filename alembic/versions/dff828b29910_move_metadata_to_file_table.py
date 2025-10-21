"""move_metadata_to_file_table

Revision ID: dff828b29910
Revises: d2d008e51d95
Create Date: 2025-10-21 18:59:37.859670

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'dff828b29910'
down_revision: Union[str, None] = 'd2d008e51d95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add file_metadata column to files table
    op.add_column('files', sa.Column('file_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Step 2: Migrate data from file_metadata table to files.file_metadata
    # This copies the metadata_json from file_metadata table to files.file_metadata
    op.execute("""
        UPDATE files 
        SET file_metadata = fm.metadata
        FROM file_metadata fm
        WHERE files.id = fm.file_id
    """)
    
    # Step 3: Drop file_metadata table (CASCADE will drop the index too)
    op.drop_index('idx_file_metadata_file_id', table_name='file_metadata')
    op.drop_table('file_metadata')


def downgrade() -> None:
    # Step 1: Recreate file_metadata table
    op.create_table('file_metadata',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('file_id', sa.UUID(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['file_id'], ['files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_file_metadata_file_id', 'file_metadata', ['file_id'], unique=False)
    
    # Step 2: Migrate data back from files.file_metadata to file_metadata table
    op.execute("""
        INSERT INTO file_metadata (id, file_id, metadata, created_at, updated_at)
        SELECT 
            gen_random_uuid(),
            id,
            file_metadata,
            created_at,
            updated_at
        FROM files
        WHERE file_metadata IS NOT NULL
    """)
    
    # Step 3: Drop file_metadata column from files table
    op.drop_column('files', 'file_metadata')
