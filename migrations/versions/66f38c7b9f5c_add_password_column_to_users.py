"""add password column to users

Revision ID: 66f38c7b9f5c
Revises: 2d485c3cb789
Create Date: 2024-xx-xx xx:xx:xx.xxxxxx

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '66f38c7b9f5c'
down_revision = '2d485c3cb789'
branch_labels = None
depends_on = None


def upgrade():
    # Створюємо нові таблиці
    op.create_table('rewiews',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('repair_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('photo_url', sa.String(length=255), nullable=True),
    sa.Column('required_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.Enum('NEW', 'IN_PROGRESS', 'MESSAGE', 'COMPLETED', 'CANCELLED', name='request_status'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('admin_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('users_in_telegram',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tg_code', sa.String(length=50), nullable=False),
    sa.Column('user_tg_id', sa.String(length=255), nullable=False),
    sa.Column('user_in_site', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_in_site'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('admin_messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('request_id', sa.Integer(), nullable=False),
    sa.Column('admin_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['request_id'], ['repair_requests.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_messages_id'), 'admin_messages', ['id'], unique=False)
    
    # Додаємо стовпець password до users
    op.add_column('users', sa.Column('password', sa.String(length=255), nullable=False, server_default=''))
    
    # Змінюємо тип email
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=50),
               existing_nullable=False)
    
    # Видаляємо старий стовпець hash_password
    op.drop_column('users', 'hash_password')
    
    # Видаляємо унікальне обмеження username (якщо воно є)
    # op.drop_constraint('users_username_key', 'users', type_='unique')
    
    # ЗАКОМЕНТОВАНО: Не видаляємо старі таблиці, щоб уникнути проблем з залежностями
    # op.drop_table('menu')
    # op.drop_table('orders')
    # op.drop_table('order_menu')
    # op.drop_table('orders_menu')
    # op.drop_table('reservations')
    # op.drop_table('reviews')


def downgrade():
    # У разі відкату
    op.add_column('users', sa.Column('hash_password', sa.VARCHAR(length=255), autoincrement=False, nullable=False))
    op.alter_column('users', 'email',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=100),
               existing_nullable=False)
    op.drop_column('users', 'password')
    op.drop_index(op.f('ix_admin_messages_id'), table_name='admin_messages')
    op.drop_table('admin_messages')
    op.drop_table('users_in_telegram')
    op.drop_table('repair_requests')
    op.drop_table('rewiews')