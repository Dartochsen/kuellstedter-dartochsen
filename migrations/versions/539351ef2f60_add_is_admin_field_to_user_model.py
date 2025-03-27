"""Add is_admin field to User model

Revision ID: 539351ef2f60
Revises: 51a07edf3e36
Create Date: 2025-03-02 22:13:34.515462

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '539351ef2f60'
down_revision = '51a07edf3e36'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns('user')
    if 'is_admin' not in [c['name'] for c in columns]:
        op.add_column('user', sa.Column('is_admin', sa.Boolean(), nullable=True))
    
    # Entfernen Sie die folgenden Zeilen, da sie Tabellen löschen, die wahrscheinlich benötigt werden
    # op.drop_table('user')
    # op.drop_table('forum_antwort')
    # op.drop_table('post')
    # op.drop_table('forum_thema')
    # op.drop_table('player')
    # op.drop_table('game')
    # op.drop_table('event')

    # Behalten Sie die Änderungen an game_players und throw_data bei
    with op.batch_alter_table('game_players', schema=None) as batch_op:
        batch_op.create_index('idx_game_players_score', ['game_id', 'player_id', 'score'], unique=False)
        batch_op.drop_constraint('game_players_game_id_fkey', type_='foreignkey')
        batch_op.drop_constraint('game_players_player_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'games', ['game_id'], ['id'])
        batch_op.create_foreign_key(None, 'players', ['player_id'], ['id'])

    with op.batch_alter_table('throw_data', schema=None) as batch_op:
        batch_op.add_column(sa.Column('game_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_throw_data_game_id'), ['game_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_throw_data_player_id'), ['player_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_throw_data_timestamp'), ['timestamp'], unique=False)
        batch_op.drop_constraint('throw_data_player_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'players', ['player_id'], ['id'])
        batch_op.create_foreign_key(None, 'games', ['game_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('throw_data', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('throw_data_player_id_fkey', 'player', ['player_id'], ['id'])
        batch_op.drop_index(batch_op.f('ix_throw_data_timestamp'))
        batch_op.drop_index(batch_op.f('ix_throw_data_player_id'))
        batch_op.drop_index(batch_op.f('ix_throw_data_game_id'))
        batch_op.drop_column('game_id')

    with op.batch_alter_table('game_players', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('game_players_player_id_fkey', 'player', ['player_id'], ['id'])
        batch_op.create_foreign_key('game_players_game_id_fkey', 'game', ['game_id'], ['id'])
        batch_op.drop_index('idx_game_players_score')

    # Entfernen Sie die is_admin Spalte
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('is_admin')

    # ### end Alembic commands ###
