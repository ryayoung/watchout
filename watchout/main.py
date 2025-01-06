import os
import asyncio
import click
from click import echo, style
from watchfiles import awatch
from prompt_toolkit.keys import Keys
from watchout.config import RunDetail, Config, Global
from watchout.status import get_status_bar
from watchout.runner import run_command


@click.command()
@click.argument('script_path', type=click.Path(exists=True))
@click.option('--lazy', is_flag=True, default=False)
@click.option('--keep-duplicates', is_flag=True, default=False)
@click.option('--no-watch', is_flag=True, default=False)
@click.option('--verbose', is_flag=True, default=False)
def main(script_path, lazy, keep_duplicates, no_watch, verbose):
    Global.config = Config(
        path=script_path,
        lazy=lazy,
        keep_duplicates=keep_duplicates,
        no_watch=no_watch,
        verbose=verbose,
    )
    Global.name = os.path.splitext(os.path.basename(Global.config.path))[0]
    script_path = os.path.abspath(script_path)
    click.clear()

    if Global.config.no_watch:
        echo(get_status_bar(0, 0))
        echo(style('Press Enter to run', fg='white', dim=True, italic=True))
    else:
        run_script()
    asyncio.run(run())


async def run():
    watch_task: asyncio.Task | None = None
    if not Global.config.no_watch:
        watch_task = asyncio.create_task(watch_file_and_run())

    def handle_input():
        keypresses = Global.input.read_keys()
        if not keypresses:
            return
        key = keypresses[-1].key

        if key in [Keys.ControlC, 'q']:
            Global.done.set()
        else:
            handle_key(key)

    with Global.input.raw_mode():
        with Global.input.attach(handle_input):
            await Global.done.wait()

    if watch_task:
        watch_task.cancel()
        await watch_task


async def watch_file_and_run():
    try:
        async for _ in awatch(Global.config.path, debounce=0):
            run_script()
    except asyncio.CancelledError:
        pass


def handle_key(key: Keys | str):

    if key in [Keys.Enter]:
        run_script()
        return

    index, history_size = Global.index, len(Global.history)

    if key in [Keys.Down, 'j']:
        index = min(index + 1, history_size - 1)
    elif key in [Keys.Up, 'k']:
        index = max(index - 1, 0)

    Global.index = index
    render_current()


def render_current():
    click.clear()
    detail = Global.history[Global.index]
    echo(
        get_status_bar(
            Global.index + 1,
            len(Global.history),
            run_detail=detail,
        )
    )
    echo(detail.output)


def run_script():
    click.clear()
    count = len(Global.history)
    echo(get_status_bar(count + 1, count or 1, is_running=True))

    last_run: RunDetail | None = Global.history[-1] if Global.history else None

    if Global.config.lazy and last_run:
        echo(last_run.output)
        result = run_command(['python', Global.config.path])
    else:
        result = run_command(['python', Global.config.path], display=True)

    same_as_last_output = last_run and result.output == last_run.output

    if last_run and same_as_last_output and not Global.config.keep_duplicates:
        Global.history[-1] = RunDetail(
            output=last_run.output,
            duration=result.duration,
            timestamp=result.timestamp,
            failed=result.failed,
            repeats=last_run.repeats + 1,
        )
    else:
        Global.history.append(result)

    Global.index = len(Global.history) - 1
    render_current()
