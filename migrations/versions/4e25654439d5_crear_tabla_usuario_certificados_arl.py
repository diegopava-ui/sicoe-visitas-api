"""crear tabla usuario_certificados_arl

Revision ID: 4e25654439d5
Revises: a7f3c1d9e2b4
Create Date: 2026-08-24 17:24:45.517427

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4e25654439d5'
down_revision: Union[str, Sequence[str], None] = 'a7f3c1d9e2b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('usuario_certificados_arl',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('nombre_archivo', sa.String(length=255), nullable=False),
    sa.Column('url_archivo', sa.Text(), nullable=False),
    sa.Column('fecha_vigencia', sa.Date(), nullable=True),
    sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('updated_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['usuarios.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['usuarios.id'], ),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usuario_certificados_arl_created_by'), 'usuario_certificados_arl', ['created_by'], unique=False)
    op.create_index(op.f('ix_usuario_certificados_arl_updated_by'), 'usuario_certificados_arl', ['updated_by'], unique=False)
    op.create_index(op.f('ix_usuario_certificados_arl_usuario_id'), 'usuario_certificados_arl', ['usuario_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_usuario_certificados_arl_usuario_id'), table_name='usuario_certificados_arl')
    op.drop_index(op.f('ix_usuario_certificados_arl_updated_by'), table_name='usuario_certificados_arl')
    op.drop_index(op.f('ix_usuario_certificados_arl_created_by'), table_name='usuario_certificados_arl')
    op.drop_table('usuario_certificados_arl')