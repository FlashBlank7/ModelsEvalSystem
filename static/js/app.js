// 全局配置
const API_BASE = 'http://localhost:9000';

// 工具函数
const utils = {
    // 显示通知
    showNotification: function(message, type = 'info', duration = 3000) {
        const notifications = document.getElementById('notifications');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        notifications.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, duration);
    },
    
    // 显示/隐藏加载状态
    showLoading: function(show = true) {
        const loading = document.getElementById('loading');
        if (show) {
            loading.style.display = 'flex';
        } else {
            loading.style.display = 'none';
        }
    },
    
    // 显示模态框
    showModal: function(title, content) {
        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-body').innerHTML = content;
        document.getElementById('modal').style.display = 'block';
    },
    
    // 隐藏模态框
    hideModal: function() {
        document.getElementById('modal').style.display = 'none';
    },
    
    // 格式化日期
    formatDate: function(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN');
    },
    
    // 格式化执行时间
    formatExecutionTime: function(seconds) {
        if (!seconds) return '-';
        if (seconds < 60) return `${seconds.toFixed(1)}秒`;
        if (seconds < 3600) return `${(seconds / 60).toFixed(1)}分钟`;
        return `${(seconds / 3600).toFixed(1)}小时`;
    },
    
    // 格式化内存使用量
    formatMemory: function(mb) {
        if (!mb) return '-';
        if (mb < 1024) return `${mb.toFixed(1)} MB`;
        return `${(mb / 1024).toFixed(1)} GB`;
    },
    
    // API请求封装
    apiRequest: async function(url, options = {}) {
        console.log(url, options)
        try {
            const response = await fetch(`${API_BASE}${url}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API请求失败:', error);
            utils.showNotification(`请求失败: ${error.message}`, 'error');
            throw error;
        }
    }
};

// 导航栏管理
const navigation = {
    init: function() {
        const navItems = document.querySelectorAll('.nav-item');
        const contentSections = document.querySelectorAll('.content-section');
        
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const targetSection = item.dataset.section;
                
                // 更新导航状态
                navItems.forEach(nav => nav.classList.remove('active'));
                item.classList.add('active');
                
                // 显示目标内容区域
                contentSections.forEach(section => section.classList.remove('active'));
                document.getElementById(targetSection).classList.add('active');
                
                // 加载对应数据
                this.loadSectionData(targetSection);
            });
        });
    },
    
    loadSectionData: function(section) {
        switch(section) {
            case 'dashboard':
                dashboard.loadData();
                break;
            case 'models':
                models.loadData();
                break;
            case 'datasets':
                datasets.loadData();
                break;
            case 'evaluation':
                evaluation.loadData();
                break;
            case 'records':
                records.loadData();
                break;
            case 'monitoring':
                monitoring.loadData();
                break;
        }
    }
};

// 仪表板
const dashboard = {
    loadData: function() {
        this.loadStats();
        this.loadRecentActivities();
    },
    
    loadStats: async function() {
        try {
            const [models, datasets, records, gpu] = await Promise.all([
                utils.apiRequest('/api/models'),
                utils.apiRequest('/api/datasets'),
                utils.apiRequest('/api/records?limit=100'),
                utils.apiRequest('/api/monitoring/gpu/status')
            ]);
            
            document.getElementById('total-models').textContent = models.data?.length || 0;
            document.getElementById('total-datasets').textContent = datasets.data?.length || 0;
            document.getElementById('total-evaluations').textContent = records.data?.length || 0;
            
            // GPU使用率
            const gpuUsage = gpu.data?.gpus?.[0]?.utilization_gpu || 0;
            document.getElementById('gpu-usage').textContent = `${gpuUsage}%`;
        } catch (error) {
            console.error('加载统计数据失败:', error);
        }
    },
    
    loadRecentActivities: async function() {
        try {
            const response = await utils.apiRequest('/api/records?limit=10');
            const activities = response.data || [];
            
            const container = document.getElementById('recent-activities');
            container.innerHTML = activities.map(activity => `
                <div class="activity-item">
                    <div class="activity-title">${activity.model_name} - ${activity.dataset_name}</div>
                    <div class="activity-meta">
                        分数: ${activity.score || '-'} | 
                        类型: ${activity.model_type} | 
                        时间: ${utils.formatDate(activity.created_at)}
                    </div>
                </div>
            `).join('') || '<p>暂无最近活动</p>';
        } catch (error) {
            console.error('加载最近活动失败:', error);
        }
    }
};

// 模型管理
const models = {
    selectedModel: null,
    
    loadData: function() {
        this.loadModels();
        this.initEventListeners();
    },
    
    loadModels: async function() {
        try {
            utils.showLoading(true);
            const response = await utils.apiRequest('/api/models');
            
            // 1. 获取原始数据（处理不同的后端嵌套习惯）
            let rawData = response.data || response; 
            console.log("原始数据:", rawData); // 调试用
            
            // 2. 核心修复：强制转为数组
            let modelsList = [];
            if (Array.isArray(rawData)) {
                // 如果已经是数组，直接用
                modelsList = rawData;
            } else if (rawData && typeof rawData === 'object') {
                // 如果是对象/字典，取其所有 Value 组成数组
                modelsList = Object.values(rawData);
            }

            console.log("解析后的模型列表:", modelsList); // 调试用

            const container = document.getElementById('models-list');
            // 3. 使用清洗后的 modelsList 进行渲染
            container.innerHTML = modelsList.map(model => `
                <div class="model-card ${this.selectedModel === model.path ? 'selected' : ''}" 
                    data-path="${model.path || ''}">
                    <div class="model-header">
                        <div class="model-icon"><i class="fas fa-robot"></i></div>
                        <div class="model-info">
                            <h3>${model.name || '未命名模型'}</h3>
                            <span class="model-type">${model.type || '未知类型'}</span>
                        </div>
                    </div>
                    <div class="model-details">
                        <p><strong>路径:</strong> ${model.path || '-'}</p>
                        <p><strong>参数:</strong> ${model.parameters?.toLocaleString() || '未知'}</p>
                    </div>
                </div>
            `).join('') || '<p>暂无模型数据</p>';
            
            // 重新绑定点击事件
            container.querySelectorAll('.model-card').forEach(card => {
                card.addEventListener('click', () => this.selectModel(card.dataset.path));
            });

        } catch (error) {
            console.error('加载模型数据失败:', error);
            utils.showNotification('加载模型数据失败', 'error');
        } finally {
            utils.showLoading(false);
        }
    },
    
    selectModel: function(path) {
        this.selectedModel = path;
        
        // 更新UI
        document.querySelectorAll('.model-card').forEach(card => {
            card.classList.remove('selected');
        });
        document.querySelector(`[data-path="${path}"]`).classList.add('selected');
        
        utils.showNotification(`已选择模型: ${path}`, 'success');
    },
    
    initEventListeners: function() {
        const scanBtn = document.getElementById('scan-models');
        if (scanBtn && !scanBtn.dataset.initialized) {
            scanBtn.addEventListener('click', () => {
                this.scanModels();
            });
            scanBtn.dataset.initialized = 'true';
        }
    },
    
    scanModels: async function() {
        try {
            utils.showLoading(true);
            await utils.apiRequest('/api/models/scan', { method: 'POST' });
            utils.showNotification('模型扫描完成', 'success');
            this.loadModels();
        } catch (error) {
            console.error('扫描模型失败:', error);
        } finally {
            utils.showLoading(false);
        }
    }
};

// 数据集管理
const datasets = {
    loadData: function() {
        this.loadDatasets();
    },
    
    loadDatasets: async function() {
        try {
            const response = await utils.apiRequest('/api/datasets');
            const datasets = response.data || [];
            
            const container = document.getElementById('datasets-list');
            container.innerHTML = datasets.map(dataset => `
                <div class="dataset-card ${dataset.status}">
                    <div class="dataset-header">
                        <div class="dataset-icon">
                            <i class="fas fa-database"></i>
                        </div>
                        <div class="dataset-info">
                            <h3>${dataset.name}</h3>
                            <span class="dataset-status ${dataset.status}">${this.getStatusText(dataset.status)}</span>
                        </div>
                    </div>
                    <div class="dataset-details">
                        <p><strong>描述:</strong> ${dataset.description || '无'}</p>
                        <p><strong>任务类型:</strong> ${dataset.task || '未知'}</p>
                        <p><strong>样本数量:</strong> ${dataset.samples?.toLocaleString() || '未知'}</p>
                        <p><strong>验证时间:</strong> ${utils.formatDate(dataset.last_validated)}</p>
                    </div>
                </div>
            `).join('') || '<p>暂无数据集数据</p>';
        } catch (error) {
            console.error('加载数据集数据失败:', error);
            utils.showNotification('加载数据集数据失败', 'error');
        }
    },
    
    getStatusText: function(status) {
        const statusMap = {
            'validated': '已验证',
            'error': '错误',
            'pending': '待验证'
        };
        return statusMap[status] || status;
    }
};

// 测评执行
const evaluation = {
    init: function() {
        this.initTabs();
        this.initForms();
        this.initEventListeners();
        this.startProgressPolling();
    },
    
    loadData: function() {
        this.populateModelSelects();
        this.loadTaskProgress();
    },
    
    initTabs: function() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.dataset.tab;
                
                // 更新按钮状态
                tabBtns.forEach(tab => tab.classList.remove('active'));
                btn.classList.add('active');
                
                // 显示对应内容
                tabContents.forEach(content => content.classList.remove('active'));
                document.getElementById(`${targetTab}-evaluation`).classList.add('active');
            });
        });
    },
    
    initForms: function() {
        // 单模型测评表单
        const singleForm = document.getElementById('single-evaluation-form');
        if (singleForm && !singleForm.dataset.initialized) {
            singleForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitSingleEvaluation();
            });
            singleForm.dataset.initialized = 'true';
        }
        
        // 批量测评表单
        const batchForm = document.getElementById('batch-evaluation-form');
        if (batchForm && !batchForm.dataset.initialized) {
            batchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitBatchEvaluation();
            });
            batchForm.dataset.initialized = 'true';
        }
    },
    
    initEventListeners: function() {
        // 监听模型数据加载完成
        document.addEventListener('modelsLoaded', () => {
            this.populateModelSelects();
        });
    },
    
    populateModelSelects: async function() {
        try {
            const response = await utils.apiRequest('/api/models');
            const models = response.data || [];
            
            // 单模型选择
            const modelSelect = document.getElementById('model-select');
            if (modelSelect) {
                modelSelect.innerHTML = '<option value="">请选择模型</option>' +
                    models.map(model => `<option value="${model.path}">${model.name}</option>`).join('');
            }
            
            // 批量模型选择
            const batchModels = document.getElementById('batch-models');
            if (batchModels) {
                batchModels.innerHTML = models.map(model => `
                    <div class="checkbox-item">
                        <input type="checkbox" id="model-${model.path}" value="${model.path}">
                        <label for="model-${model.path}">${model.name}</label>
                    </div>
                `).join('');
            }
            
            // 触发事件
            document.dispatchEvent(new CustomEvent('modelsLoaded'));
        } catch (error) {
            console.error('加载模型选择器失败:', error);
        }
    },
    
    submitSingleEvaluation: async function() {
        const form = document.getElementById('single-evaluation-form');
        const formData = new FormData(form);
        
        const modelPath = formData.get('model-select') || document.getElementById('model-select').value;
        const datasetName = document.getElementById('dataset-input').value;
        const configText = document.getElementById('config-json').value.trim();
        
        if (!modelPath || !datasetName) {
            utils.showNotification('请填写模型和数据集', 'warning');
            return;
        }
        
        let config = null;
        if (configText) {
            try {
                config = JSON.parse(configText);
            } catch (error) {
                utils.showNotification('配置参数JSON格式错误', 'error');
                return;
            }
        }
        
        try {
            utils.showLoading(true);
            const response = await utils.apiRequest('/api/evaluation/single', {
                method: 'POST',
                body: JSON.stringify({
                    model_path: modelPath,
                    dataset_name: datasetName,
                    config: config
                })
            });
            
            if (response.success) {
                utils.showNotification('单模型测评任务已创建', 'success');
                form.reset();
                this.loadTaskProgress();
            } else {
                utils.showNotification(`创建测评任务失败: ${response.detail}`, 'error');
            }
        } catch (error) {
            console.error('提交单模型测评失败:', error);
        } finally {
            utils.showLoading(false);
        }
    },
    
    submitBatchEvaluation: async function() {
        const form = document.getElementById('batch-evaluation-form');
        const formData = new FormData(form);
        
        const selectedModels = Array.from(document.querySelectorAll('#batch-models input[type="checkbox"]:checked'))
            .map(cb => cb.value);
        const datasetName = document.getElementById('batch-dataset-input').value;
        const taskName = document.getElementById('task-name').value;
        const parallel = document.getElementById('parallel-execution').value === 'true';
        
        if (selectedModels.length === 0) {
            utils.showNotification('请选择至少一个模型', 'warning');
            return;
        }
        
        if (!datasetName) {
            utils.showNotification('请填写数据集名称', 'warning');
            return;
        }
        
        try {
            utils.showLoading(true);
            const response = await utils.apiRequest('/api/evaluation/batch', {
                method: 'POST',
                body: JSON.stringify({
                    model_paths: selectedModels,
                    dataset_name: datasetName,
                    task_name: taskName,
                    parallel: parallel
                })
            });
            
            if (response.success) {
                utils.showNotification('批量测评任务已创建', 'success');
                form.reset();
                this.loadTaskProgress();
            } else {
                utils.showNotification(`创建批量测评失败: ${response.detail}`, 'error');
            }
        } catch (error) {
            console.error('提交批量测评失败:', error);
        } finally {
            utils.showLoading(false);
        }
    },
    
    loadTaskProgress: async function() {
        try {
            const response = await utils.apiRequest('/api/evaluation/tasks');
            const tasks = response.data || [];
            
            const container = document.getElementById('task-progress');
            container.innerHTML = tasks.map(task => `
                <div class="progress-item">
                    <div class="progress-title">${task.task_name || '未命名任务'}</div>
                    <div class="progress-meta">
                        模型: ${task.model_count} | 状态: ${task.status} | 
                        创建时间: ${utils.formatDate(task.created_at)}
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${task.progress || 0}%"></div>
                    </div>
                </div>
            `).join('') || '<p>暂无测评任务</p>';
        } catch (error) {
            console.error('加载任务进度失败:', error);
        }
    },
    
    startProgressPolling: function() {
        // 每5秒更新一次任务进度
        setInterval(() => {
            if (document.getElementById('task-progress')) {
                this.loadTaskProgress();
            }
        }, 5000);
    }
};

// 测评记录
const records = {
    loadData: function() {
        this.loadRecords();
        this.initEventListeners();
    },
    
    loadRecords: async function(page = 1, limit = 50) {
        try {
            utils.showLoading(true);
            const response = await utils.apiRequest(`/api/records?page=${page}&limit=${limit}`);
            const records = response.data || [];
            
            const tbody = document.querySelector('#records-table tbody');
            tbody.innerHTML = records.map(record => `
                <tr>
                    <td>${record.id}</td>
                    <td>${record.model_name}</td>
                    <td>${record.dataset_name}</td>
                    <td>${record.score || '-'}</td>
                    <td>${record.model_type}</td>
                    <td><span class="status-badge status-${record.status}">${this.getStatusText(record.status)}</span></td>
                    <td>${utils.formatExecutionTime(record.execution_time)}</td>
                    <td>
                        <button class="btn btn-secondary" onclick="records.viewRecord(${record.id})">查看</button>
                        ${record.status === 'completed' ? `<button class="btn btn-primary" onclick="records.addToExcellent(${record.id})">加入优秀</button>` : ''}
                    </td>
                </tr>
            `).join('') || '<tr><td colspan="8">暂无测评记录</td></tr>';
        } catch (error) {
            console.error('加载测评记录失败:', error);
            utils.showNotification('加载测评记录失败', 'error');
        } finally {
            utils.showLoading(false);
        }
    },
    
    getStatusText: function(status) {
        const statusMap = {
            'completed': '已完成',
            'running': '运行中',
            'failed': '失败',
            'pending': '等待中'
        };
        return statusMap[status] || status;
    },
    
    viewRecord: async function(recordId) {
        try {
            const response = await utils.apiRequest(`/api/records/${recordId}`);
            const record = response.data;
            
            const content = `
                <div class="record-details">
                    <h3>测评详情</h3>
                    <p><strong>模型:</strong> ${record.model_name}</p>
                    <p><strong>数据集:</strong> ${record.dataset_name}</p>
                    <p><strong>分数:</strong> ${record.score || '-'}</p>
                    <p><strong>模型类型:</strong> ${record.model_type}</p>
                    <p><strong>状态:</strong> ${this.getStatusText(record.status)}</p>
                    <p><strong>执行时间:</strong> ${utils.formatExecutionTime(record.execution_time)}</p>
                    <p><strong>内存使用:</strong> ${utils.formatMemory(record.memory_usage)}</p>
                    <p><strong>创建时间:</strong> ${utils.formatDate(record.created_at)}</p>
                    ${record.error_message ? `<p><strong>错误信息:</strong> ${record.error_message}</p>` : ''}
                    ${record.metrics ? `<p><strong>详细指标:</strong> <pre>${JSON.stringify(record.metrics, null, 2)}</pre></p>` : ''}
                </div>
            `;
            
            utils.showModal('测评记录详情', content);
        } catch (error) {
            console.error('获取记录详情失败:', error);
            utils.showNotification('获取记录详情失败', 'error');
        }
    },
    
    addToExcellent: async function(recordId) {
        try {
            const reason = prompt('请输入加入优秀记录的理由（可选）:');
            
            const response = await utils.apiRequest(`/api/records/${recordId}/excellent`, {
                method: 'POST',
                body: JSON.stringify({
                    reason: reason,
                    category: 'general'
                })
            });
            
            if (response.success) {
                utils.showNotification('已加入优秀记录', 'success');
                this.loadRecords();
            } else {
                utils.showNotification('加入优秀记录失败', 'error');
            }
        } catch (error) {
            console.error('加入优秀记录失败:', error);
        }
    },
    
    initEventListeners: function() {
        // 搜索功能
        const searchInput = document.getElementById('search-input');
        if (searchInput && !searchInput.dataset.initialized) {
            searchInput.addEventListener('input', utils.debounce(() => {
                this.searchRecords();
            }, 500));
            searchInput.dataset.initialized = 'true';
        }
        
        // 模型类型过滤
        const modelTypeFilter = document.getElementById('model-type-filter');
        if (modelTypeFilter && !modelTypeFilter.dataset.initialized) {
            modelTypeFilter.addEventListener('change', () => {
                this.filterRecords();
            });
            modelTypeFilter.dataset.initialized = 'true';
        }
        
        // 导出功能
        const exportBtn = document.getElementById('export-records');
        if (exportBtn && !exportBtn.dataset.initialized) {
            exportBtn.addEventListener('click', () => {
                this.exportRecords();
            });
            exportBtn.dataset.initialized = 'true';
        }
    },
    
    searchRecords: function() {
        const query = document.getElementById('search-input').value;
        // 实现搜索逻辑
        console.log('搜索:', query);
    },
    
    filterRecords: function() {
        const modelType = document.getElementById('model-type-filter').value;
        // 实现过滤逻辑
        console.log('过滤:', modelType);
    },
    
    exportRecords: function() {
        // 实现导出功能
        utils.showNotification('导出功能开发中...', 'info');
    }
};

// 系统监控
const monitoring = {
    loadData: function() {
        this.loadGPUStatus();
        this.loadNvidiaSMI();
        this.loadSystemInfo();
        this.initChart();
        this.startAutoRefresh();
    },
    
    loadGPUStatus: async function() {
        try {
            const response = await utils.apiRequest('/api/monitoring/gpu/status');
            const gpuData = response.data;
            
            const container = document.getElementById('gpu-status');
            container.innerHTML = gpuData.gpus ? gpuData.gpus.map(gpu => `
                <div class="gpu-info">
                    <p><strong>GPU ${gpu.index}:</strong> ${gpu.name}</p>
                    <p><strong>利用率:</strong> ${gpu.utilization_gpu}%</p>
                    <p><strong>显存使用:</strong> ${gpu.memory_used}MB / ${gpu.memory_total}MB</p>
                    <p><strong>温度:</strong> ${gpu.temperature_gpu}°C</p>
                    <p><strong>功耗:</strong> ${gpu.power_draw}W</p>
                </div>
            `).join('') : '<p>未检测到GPU</p>';
        } catch (error) {
            console.error('加载GPU状态失败:', error);
        }
    },
    
    loadNvidiaSMI: async function() {
        try {
            const response = await utils.apiRequest('/api/monitoring/nvidia-smi');
            const container = document.getElementById('nvidia-smi-output');
            container.textContent = response.data.output || '无法获取nvidia-smi输出';
        } catch (error) {
            console.error('加载nvidia-smi输出失败:', error);
        }
    },
    
    
    loadSystemInfo: async function() {
        try {
            const response = await utils.apiRequest('/api/monitoring/system/info');
            const systemData = response.data;
            
            const container = document.getElementById('system-info');
            container.innerHTML = `
                <p><strong>CPU使用率:</strong> ${systemData.cpu_usage}%</p>
                <p><strong>内存使用:</strong> ${systemData.memory_usage}MB / ${systemData.memory_total}MB</p>
                <p><strong>磁盘使用:</strong> ${systemData.disk_usage}GB / ${systemData.disk_total}GB</p>
                <p><strong>系统负载:</strong> ${systemData.load_average}</p>
                <p><strong>运行时间:</strong> ${systemData.uptime}</p>
            `;
        } catch (error) {
            console.error('加载系统信息失败:', error);
        }
    },
    
    initChart: function() {
        const ctx = document.getElementById('gpu-chart');
        if (!ctx) return;
        
        this.gpuChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'GPU使用率',
                    data: [],
                    borderColor: 'rgb(102, 126, 234)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                animation: {
                    duration: 0
                }
            }
        });
    },
    
    startAutoRefresh: function() {
        // 每10秒更新监控数据
        setInterval(() => {
            if (document.getElementById('gpu-status')) {
                this.loadGPUStatus();
                this.updateChart();
                this.loadSystemInfo();
            }
        }, 10000);
    },
    
    updateChart: function() {
        if (!this.gpuChart) return;
        
        // 添加新数据点
        const now = new Date().toLocaleTimeString();
        const gpuData = document.querySelector('#gpu-status .gpu-info');
        
        if (gpuData) {
            const utilization = gpuData.querySelector('p:nth-child(2)').textContent.match(/(\d+)%/);
            const value = utilization ? parseInt(utilization[1]) : 0;
            
            this.gpuChart.data.labels.push(now);
            this.gpuChart.data.datasets[0].data.push(value);
            
            // 保持最近20个数据点
            if (this.gpuChart.data.labels.length > 20) {
                this.gpuChart.data.labels.shift();
                this.gpuChart.data.datasets[0].data.shift();
            }
            
            this.gpuChart.update('none');
        }
    }
};

// 工具函数增强
utils.debounce = function(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

// 模态框事件
document.addEventListener('DOMContentLoaded', function() {
    // 关闭模态框
    document.querySelector('.close').addEventListener('click', utils.hideModal);
    document.getElementById('modal-close').addEventListener('click', utils.hideModal);
    
    // 点击模态框外部关闭
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('modal');
        if (event.target === modal) {
            utils.hideModal();
        }
    });
    
    // 初始化应用
    initApp();
});

function initApp() {
    // 初始化导航
    navigation.init();
    
    // 初始化各个模块
    dashboard.loadData();
    models.loadData();
    datasets.loadData();
    evaluation.init();
    records.loadData();
    monitoring.loadData();
    
    utils.showNotification('系统初始化完成', 'success');
}
