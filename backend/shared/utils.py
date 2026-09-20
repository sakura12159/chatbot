import time
from pathlib import Path
from typing import Literal

def get_root_directory() -> Path:
    """
    获取当前项目的根目录
    returns: Path
        项目根目录
    """
    return Path(__file__).resolve().parent.parent.parent

def get_time_duration(
    start_time: float,
    unit: Literal['s', 'ms', 'ns'] = 'ms',
    ndigits: int = 2
) -> float:
    """
    计算持续时间
    Args:
        start_time (float):         开始时间
        unit (Literal['s', 'ms']):  单位
        ndigits (int):              保留小数位数
    Returns: float
        持续的时间
    """
    delta = time.perf_counter() - start_time
    if unit == 's':
        return round(delta, ndigits=ndigits)
    elif unit =='ms':
        return round(delta * 1000, ndigits=ndigits)
    return round(delta * 1000000, ndigits=ndigits)
