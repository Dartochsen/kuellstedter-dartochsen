"""Add is_member field to User model

Revision ID: 37cdf65ebb9c
Revises: df95310a7fa3
Create Date: 2025-02-28 19:36:11.612332

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '37cdf65ebb9c'
down_revision = 'df95310a7fa3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('event',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('forum_thema',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('titel', sa.String(length=150), nullable=False),
    sa.Column('inhalt', sa.Text(), nullable=False),
    sa.Column('autor', sa.String(length=100), nullable=False),
    sa.Column('datum', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('player',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('date_of_birth', sa.Date(), nullable=True),
    sa.Column('join_date', sa.DateTime(), nullable=True),
    sa.Column('average_score', sa.Float(), nullable=True),
    sa.Column('games_played', sa.Integer(), nullable=True),
    sa.Column('training_hours', sa.Float(), nullable=True),
    sa.Column('highest_score', sa.Integer(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    with op.batch_alter_table('player', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_player_name'), ['name'], unique=True)

    op.create_table('post',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=150), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('author', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('antwort',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('inhalt', sa.Text(), nullable=False),
    sa.Column('autor', sa.String(length=100), nullable=False),
    sa.Column('thema_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['thema_id'], ['forum_thema.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('throw_data',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.Column('angle', sa.Float(), nullable=False),
    sa.Column('velocity', sa.Float(), nullable=False),
    sa.Column('accuracy', sa.Float(), nullable=False),
    sa.Column('score', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('game_type', sa.String(length=50), nullable=True),
    sa.Column('target_segment', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['player_id'], ['player.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('game_players',
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.Column('score', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['game.id'], ),
    sa.ForeignKeyConstraint(['player_id'], ['player.id'], ),
    sa.PrimaryKeyConstraint('game_id', 'player_id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_member', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('is_admin', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('is_admin')
        batch_op.drop_column('is_member')

    op.drop_table('game_players')
    op.drop_table('throw_data')
    op.drop_table('antwort')
    op.drop_table('post')
    with op.batch_alter_table('player', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_player_name'))

    op.drop_table('player')
    op.drop_table('forum_thema')
    op.drop_table('event')
    # ### end Alembic commands ###
