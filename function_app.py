import logging
import sys
import azure.functions as func

from main import main as cli_main

app = func.FunctionApp()


@app.schedule(schedule="0 0 * * * *", arg_name="mytimer", run_on_startup=False, use_monitor=True)
def support_updates(mytimer: func.TimerRequest) -> None:
    logging.info("Azure timer triggered: support_updates")
    try:
        sys.argv = ["main.py", "updates"]
        cli_main()
    except Exception:
        logging.exception("support_updates failed")
        raise


@app.schedule(schedule="0 0 3 * * *", arg_name="mytimer", run_on_startup=False, use_monitor=True)
def support_cleanup(mytimer: func.TimerRequest) -> None:
    logging.info("Azure timer triggered: support_cleanup")
    try:
        sys.argv = ["main.py", "cleanup"]
        cli_main()
    except Exception:
        logging.exception("support_cleanup failed")
        raise
