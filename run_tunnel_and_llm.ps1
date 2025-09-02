# ============================================
# 说明
# ============================================

# 1. 配置好conda环境
# 2. 安装vllm：
#     pip install "vllm>=0.5.0" torch --extra-index-url https://download.pytorch.org/whl/cu121
# 3. 下载好cloudflared.exe并设置环境变量
# 4. 在研究室电脑

# ============================================
# 配置参数
# ============================================

# 远程服务器
$User        = "zhuang"
$RemoteHost  = "gpu28"

# Conda 环境 & vLLM 参数
$CondaEnv    = "local_llm_game_translator"
$CudaDevices = "7"
$Model       = "Qwen/Qwen3-30B-A3B-Instruct-2507-FP8"
$ServeHost   = "0.0.0.0"
$ServePort   = 8000   # 服务器上vLLM的端口号
$MaxLen      = 8192
$GpuUtil     = 0.9

# SSH 端口转发
$LocalForwardPort = 9000   # 本地端口号
$RemoteForwardPort = $ServePort   # 转发端口号，即vLLM的端口号

# Cloudflare Tunnel
$TunnelUrl = "http://localhost:$LocalForwardPort"

# ============================================
# (1) 启动远程 vLLM
# ============================================
# 在服务器上开一个vLLM服务
Write-Host "Launch remote vLLM (conda run)..." -ForegroundColor Cyan

$sshCommand = "ssh -t $User@$RemoteHost conda run -n $CondaEnv --no-capture-output env CUDA_VISIBLE_DEVICES=$CudaDevices vllm serve $Model --host $ServeHost --port $ServePort --max-model-len $MaxLen --gpu-memory-utilization $GpuUtil"

Start-Process -FilePath "cmd.exe" -ArgumentList '/k', $sshCommand

Start-Sleep -Seconds 5

# ============================================
# (2) SSH 端口转发
# ============================================
# 将本地端口映射到GPU节点上的vLLM端口
Write-Host "Start SSH port-forward ($LocalForwardPort -> ${RemoteHost}:$RemoteForwardPort)..." -ForegroundColor Cyan

$portForwardCommand = "ssh -N -L ${LocalForwardPort}:localhost:$RemoteForwardPort $User@$RemoteHost"

Start-Process -FilePath "cmd.exe" -ArgumentList '/k', $portForwardCommand

Start-Sleep -Seconds 2

# ============================================
# (3) 启动 Cloudflare Tunnel (隧道工具)
# ============================================
# 将本地端口通过公网域名暴露出去，使得能从外网自由访问
Write-Host "Start Cloudflare Tunnel (expose $TunnelUrl)..." -ForegroundColor Cyan

$tunnelCommand = "cloudflared tunnel --url $TunnelUrl"

Start-Process -FilePath "cmd.exe" -ArgumentList '/k', $tunnelCommand

# ============================================
# 完成提示
# ============================================
Write-Host "Done. Three windows opened: vLLM, SSH tunnel, Cloudflare Tunnel." -ForegroundColor Green
Read-Host "Press Enter to exit..."
