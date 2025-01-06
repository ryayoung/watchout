from shutil import get_terminal_size
from click import style, unstyle
from datetime import datetime, timedelta
from humanize import naturaldelta, precisedelta
from watchout.config import RunDetail, Global


def get_status_bar(
    numerator: int,
    denominator: int,
    run_detail: RunDetail | None = None,
    is_running: bool = False,
) -> str:
    x_icon = '❌'
    power_icon = '⏻'
    progress_icon = '⬤'
    chevron_right = '⟫'
    chevron_left = '⟪'

    separator_left = style(f'  {chevron_right}  ', fg='white', dim=True)
    separator_right = style(f'  {chevron_left}  ', fg='white', dim=True)

    if numerator != denominator and run_detail is not None:
        dim = False
    else:
        dim = True

    name_part = '  ' + Global.name
    left_parts = [
        style(power_icon + name_part, fg='magenta', bold=True, dim=dim),
    ]

    if not numerator and not denominator:
        pass
    elif numerator == denominator:
        left_parts.append(style(str(numerator), fg='magenta', dim=True, bold=True))
    elif run_detail is None:
        numerator_str = style(str(numerator), fg='yellow', bold=True, dim=True)
        rest = style(f' / {denominator}', fg='white', dim=True, bold=True)
        left_parts.append(numerator_str + rest)
    else:
        numerator_str = style(str(numerator), fg='cyan', bold=True)
        rest = style(f' / {denominator}', fg='magenta')
        left_parts.append(numerator_str + rest)

    if not run_detail:
        if is_running:
            left_parts.append(style(progress_icon, fg='yellow', bold=True))
        return separator_left.join(left_parts)

    if run_detail.failed:
        left_parts.append(style(x_icon, fg='red', bold=True))

    right_parts = []

    duration_natural = custom_precisedelta(run_detail.duration)
    duration_parts = [
        style('took', fg='white', dim=dim),
        style(duration_natural, fg='white', bold=True, dim=dim),
    ]
    right_parts.append(' '.join(duration_parts))

    time_ago_delta = datetime.now() - run_detail.timestamp
    time_ago_natural = custom_naturaldelta(time_ago_delta)

    time_ago_part = ''

    if time_ago_delta.total_seconds() > 2 and time_ago_natural != duration_natural:
        time_ago_parts = []
        if Global.config.verbose:
            prefix = 'last ran' if run_detail.repeats else 'ran'
            time_ago_parts.append(style(prefix, fg='white', dim=dim))
        time_ago_parts.append(style(time_ago_natural, fg='white', bold=True, dim=dim))
        time_ago_parts.append(style('ago', fg='white', dim=dim))
        time_ago_part = ' '.join(time_ago_parts)
        right_parts.append(time_ago_part)

    repeats_part = ''

    if run_detail.repeats:
        prefix = 'repeated ' if Global.config.verbose else ''
        repeats_part = style(f'{prefix}{run_detail.repeats + 1}x', fg='white', dim=dim)
        right_parts.append(repeats_part)

    right_parts = list(reversed(right_parts))
    left_part = separator_left.join(left_parts)
    right_part = separator_right.join(right_parts) + ' '

    space_size = space_between(left_part, right_part)
    if space_size >= 2:
        middle_space = ' ' * space_size
        return f'{left_part}{middle_space}{right_part}'

    def truncate():
        nonlocal right_part, left_part, time_ago_part, repeats_part, name_part
        if name_part:
            left_part = left_part.replace(name_part, '')
            name_part = ''
        elif repeats_part:
            right_part = right_part.replace(repeats_part, '')
            repeats_part = ''
        elif time_ago_part:
            right_part = right_part.replace(time_ago_part, '')
            time_ago_part = ''
        else:
            return False
        right_part = right_part.removeprefix(separator_right)
        return True

    while truncate() and (space_size := space_between(left_part, right_part)) < 2:
        continue

    middle_space = ' ' * max(space_size, 2)
    return f'{left_part}{middle_space}{right_part}'


def custom_precisedelta(delta: timedelta) -> str:
    result = precisedelta(delta, minimum_unit='milliseconds')
    if not Global.config.verbose:
        result = (
            result.replace(' seconds', ' s')
            .replace(' milliseconds', ' ms')
            .replace(' minutes', ' mins')
        )
    result = result
    return result


def custom_naturaldelta(delta: timedelta) -> str:
    result = naturaldelta(delta, minimum_unit='milliseconds')
    if not Global.config.verbose:
        result = (
            result.replace(' seconds', ' s')
            .replace(' milliseconds', ' ms')
            .replace(' minutes', ' mins')
        )
    result = result
    return result


def visual_length(s: str) -> int:
    result = len(unstyle(s))
    if '❌' in s:
        return result + 1
    return result


def space_between(left: str, right: str) -> int:
    total_width, _ = get_terminal_size()
    left_length = visual_length(left)
    right_length = visual_length(right)
    return total_width - left_length - right_length


