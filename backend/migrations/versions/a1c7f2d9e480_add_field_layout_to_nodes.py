"""add_field_layout_to_nodes

Menandai cara field ThingSpeak sebuah node harus dibongkar. Node 1 memampatkan
arus masuk dan keluar jadi satu angka di field5 kanal pendukung dan punya valve;
Node 2 tidak. Sebelum ini ingest memperlakukan keduanya sama, sehingga field5
Node 1 tersimpan sebagai satu bilangan besar yang tidak berarti apa-apa.

Default 'node2_plain' dipilih karena itulah perilaku yang tidak mengubah apa pun
untuk baris yang sudah ada. Node 1 harus disetel manual ke 'node1_packed'.

Revision ID: a1c7f2d9e480
Revises: e62331cda815
Create Date: 2026-09-03 19:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c7f2d9e480'
down_revision: Union[str, Sequence[str], None] = 'e62331cda815'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'nodes',
        sa.Column(
            'field_layout',
            sa.String(length=32),
            nullable=False,
            server_default='node2_plain',
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('nodes', 'field_layout')
