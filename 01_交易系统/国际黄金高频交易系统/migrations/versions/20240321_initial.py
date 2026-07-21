"""initial

Revision ID: 20240321_initial
Revises: 
Create Date: 2024-03-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240321_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 创建市场数据表
    op.create_table(
        'market_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('time', sa.DateTime(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('open', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('high', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('low', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('close', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('volume', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('bid_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('ask_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建交易信号表
    op.create_table(
        'trading_signals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('time', sa.DateTime(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('signal_type', sa.String(length=20), nullable=False),
        sa.Column('direction', sa.String(length=10), nullable=False),
        sa.Column('price', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建订单表
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.String(length=50), nullable=False),
        sa.Column('time', sa.DateTime(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('order_type', sa.String(length=20), nullable=False),
        sa.Column('direction', sa.String(length=10), nullable=False),
        sa.Column('price', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('volume', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('signal_id', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['signal_id'], ['trading_signals.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id')
    )

    # 创建索引
    op.create_index('idx_market_data_time_symbol', 'market_data', ['time', 'symbol'])
    op.create_index('idx_market_data_symbol_source', 'market_data', ['symbol', 'source'])
    op.create_index('idx_trading_signals_time_symbol', 'trading_signals', ['time', 'symbol'])
    op.create_index('idx_orders_order_id', 'orders', ['order_id'])
    op.create_index('idx_orders_time_symbol', 'orders', ['time', 'symbol'])
    op.create_index('idx_orders_signal_id', 'orders', ['signal_id'])

def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_orders_signal_id')
    op.drop_index('idx_orders_time_symbol')
    op.drop_index('idx_orders_order_id')
    op.drop_index('idx_trading_signals_time_symbol')
    op.drop_index('idx_market_data_symbol_source')
    op.drop_index('idx_market_data_time_symbol')

    # 删除表
    op.drop_table('orders')
    op.drop_table('trading_signals')
    op.drop_table('market_data') 