"""
Matplotlib配置
统一管理图表生成设置，避免Tcl/Tk错误
"""

try:
    import matplotlib
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    matplotlib = None
    plt = None

import warnings

def configure_matplotlib():
    """
    配置matplotlib设置
    - 设置非交互式后端避免Tcl/Tk错误
    - 配置中文字体支持
    - 设置图表样式
    """
    if not MATPLOTLIB_AVAILABLE:
        warnings.warn("matplotlib 未安装，图表功能将被禁用")
        return
    
    # 设置非交互式后端
    matplotlib.use('Agg')
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 设置图表样式
    plt.style.use('default')
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['savefig.bbox'] = 'tight'
    
    # 忽略警告
    warnings.filterwarnings('ignore', category=UserWarning)
    warnings.filterwarnings('ignore', category=FutureWarning)


def save_chart(fig, filepath, dpi=300, bbox_inches='tight'):
    """
    保存图表到文件
    
    Args:
        fig: matplotlib图表对象
        filepath: 保存路径
        dpi: 分辨率
        bbox_inches: 边界设置
    """
    if not MATPLOTLIB_AVAILABLE:
        warnings.warn("matplotlib 未安装，无法保存图表")
        return False
        
    try:
        fig.savefig(filepath, dpi=dpi, bbox_inches=bbox_inches)
        plt.close(fig)
        return True
    except Exception as e:
        print(f"保存图表失败: {e}")
        return False


def get_matplotlib_available():
    """检查matplotlib是否可用"""
    return MATPLOTLIB_AVAILABLE


def safe_plot(func):
    """装饰器：安全执行matplotlib绘图函数"""
    def wrapper(*args, **kwargs):
        if not MATPLOTLIB_AVAILABLE:
            warnings.warn("matplotlib 未安装，跳过绘图操作")
            return None
        return func(*args, **kwargs)
    return wrapper


# 在模块导入时自动配置（如果matplotlib可用）
if MATPLOTLIB_AVAILABLE:
    configure_matplotlib()