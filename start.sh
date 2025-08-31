#!/bin/bash

# PriceSentry 快速启动脚本
# 用于快速启动和配置 PriceSentry

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查Python环境
check_python() {
    print_info "检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python版本: $python_version"
}

# 检查虚拟环境
check_venv() {
    print_info "检查虚拟环境..."
    
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_warning "未激活虚拟环境，建议使用虚拟环境"
        print_info "创建虚拟环境: python3 -m venv .venv"
        print_info "激活虚拟环境: source .venv/bin/activate"
        return 1
    fi
    
    print_success "虚拟环境已激活: $VIRTUAL_ENV"
    return 0
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    if ! command -v uv &> /dev/null; then
        print_error "uv 未安装"
        print_info "安装uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    
    print_success "依赖检查通过"
}

# 安装依赖
install_dependencies() {
    print_info "安装依赖..."
    uv sync --dev
    print_success "依赖安装完成"
}

# 检查配置文件
check_config() {
    print_info "检查配置文件..."
    
    if [[ ! -f "config/config.yaml" ]]; then
        print_warning "配置文件不存在，使用简单配置"
        cp config/config.simple.yaml config/config.yaml
        print_info "已创建简单配置文件: config/config.yaml"
        print_warning "请编辑配置文件，填入你的API密钥"
    fi
    
    # 运行配置检查
    if python3 simple_check.py; then
        print_success "配置文件检查通过"
    else
        print_warning "配置文件有问题，请检查"
    fi
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    
    mkdir -p logs
    mkdir -p config
    
    print_success "目录创建完成"
}

# 启动应用
start_app() {
    print_info "启动 PriceSentry..."
    
    # 检查是否有配置文件
    if [[ ! -f "config/config.yaml" ]]; then
        print_error "配置文件不存在"
        exit 1
    fi
    
    # 启动应用
    python3 main.py
}

# 显示帮助信息
show_help() {
    echo "PriceSentry 快速启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help      显示帮助信息"
    echo "  -c, --check     仅检查配置和环境"
    echo "  -i, --install   仅安装依赖"
    echo "  -s, --setup     完整设置（安装依赖+检查配置）"
    echo "  -d, --dev       开发模式启动"
    echo "  -p, --prod      生产模式启动"
    echo ""
    echo "示例:"
    echo "  $0              # 直接启动应用"
    echo "  $0 --setup      # 完整设置后启动"
    echo "  $0 --check      # 仅检查配置和环境"
    echo ""
}

# 主函数
main() {
    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--check)
            check_python
            check_venv
            check_dependencies
            check_config
            ;;
        -i|--install)
            check_python
            check_venv
            check_dependencies
            install_dependencies
            ;;
        -s|--setup)
            check_python
            check_venv
            check_dependencies
            install_dependencies
            create_directories
            check_config
            print_success "设置完成！"
            ;;
        -d|--dev)
            export PYTHONPATH="${PYTHONPATH}:$(pwd)"
            export LOG_LEVEL="DEBUG"
            print_info "开发模式启动"
            start_app
            ;;
        -p|--prod)
            export PYTHONPATH="${PYTHONPATH}:$(pwd)"
            export LOG_LEVEL="INFO"
            print_info "生产模式启动"
            start_app
            ;;
        "")
            print_info "快速启动 PriceSentry"
            check_python
            check_dependencies
            create_directories
            check_config
            start_app
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 捕获中断信号
trap 'print_info "脚本被中断"; exit 130' INT
trap 'print_info "脚本被终止"; exit 143' TERM

# 运行主函数
main "$@"