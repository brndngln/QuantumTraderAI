from celery import Celery
from celery.schedules import crontab
import os

# Configure Celery
app = Celery(
    'quantum_trader',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['backend.tasks.backtester', 'backend.tasks.strategy_runner']
)

# Configure task execution
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    broker_transport_options={'visibility_timeout': 3600},
    result_expires=3600,
    worker_max_tasks_per_child=100,
    task_soft_time_limit=300,
    task_time_limit=600
)

# Schedule periodic tasks
app.conf.beat_schedule = {
    'run-backtest-every-hour': {
        'task': 'backend.tasks.backtester.run_backtest',
        'schedule': crontab(minute=0),
        'args': ()
    },
    'run-strategy-every-15-minutes': {
        'task': 'backend.tasks.strategy_runner.run_strategy',
        'schedule': crontab(minute='*/15'),
        'args': ()
    },
    'update-quantum-states-every-5-minutes': {
        'task': 'backend.tasks.strategy_runner.update_quantum_states',
        'schedule': crontab(minute='*/5'),
        'args': ()
    },
    'monitor-market-every-minute': {
        'task': 'backend.tasks.strategy_runner.monitor_market',
        'schedule': crontab(minute='*'),
        'args': ()
    }
}

# Configure logging
app.conf.update(
    task_send_sent_event=True,
    task_send_started_event=True,
    task_send_success_event=True,
    task_send_failure_event=True,
    task_send_retry_event=True,
    task_send_revoked_event=True,
    task_send_timeout_event=True
)

# Configure task routing
app.conf.task_routes = {
    'backend.tasks.backtester.*': {'queue': 'backtest'},
    'backend.tasks.strategy_runner.*': {'queue': 'strategy'},
    'backend.tasks.trade_executor.*': {'queue': 'trade'},
    'backend.tasks.risk_manager.*': {'queue': 'risk'}
}

# Configure task priorities
app.conf.task_priority = {
    'backend.tasks.trade_executor.execute_trade': 10,
    'backend.tasks.risk_manager.update_risk': 9,
    'backend.tasks.strategy_runner.run_strategy': 8,
    'backend.tasks.backtester.run_backtest': 7
}

# Configure task timeouts
app.conf.task_time_limit = {
    'backend.tasks.trade_executor.execute_trade': 60,
    'backend.tasks.risk_manager.update_risk': 120,
    'backend.tasks.strategy_runner.run_strategy': 300,
    'backend.tasks.backtester.run_backtest': 3600
}

# Configure task retries
app.conf.task_retry = {
    'backend.tasks.trade_executor.execute_trade': {
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.5
    },
    'backend.tasks.risk_manager.update_risk': {
        'max_retries': 5,
        'interval_start': 0,
        'interval_step': 1,
        'interval_max': 5
    }
}
