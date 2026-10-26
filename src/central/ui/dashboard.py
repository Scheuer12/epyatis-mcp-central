"""
Dashboard Web executivo do Epyatis MCP Central (Fase 3: Multi-Usuário, Visibilidade Granular, Modelos e Kits).
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="pt-BR" class="h-full bg-slate-50">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Epyatis MCP Central</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Alpine.js CDN -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.8/dist/cdn.min.js"></script>
    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        [x-cloak] { display: none !important; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #f1f5f9; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
    </style>
</head>
<body class="h-full flex overflow-hidden text-slate-800" x-data="centralApp()" x-init="initApp()" x-cloak>

    <!-- Sidebar Lateral -->
    <aside class="w-64 bg-slate-900 text-slate-300 flex flex-col flex-shrink-0 border-r border-slate-800">
        <!-- Logo e Título -->
        <div class="h-16 flex items-center px-6 gap-3 border-b border-slate-800/80 bg-slate-950/40">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-blue-500/20 font-bold">
                <i class="fa-solid fa-cube text-lg"></i>
            </div>
            <div>
                <span class="font-bold text-white text-base tracking-wide flex items-center gap-1.5">
                    Epyatis <span class="text-xs px-1.5 py-0.5 rounded font-mono bg-blue-500/20 text-blue-400 border border-blue-500/30">MCP</span>
                </span>
                <span class="text-[11px] text-slate-400 block font-medium">Central Gateway v0.4.0</span>
            </div>
        </div>

        <!-- Links de Navegação -->
        <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            <button @click="activeTab = 'dashboard'" :class="activeTab === 'dashboard' ? 'bg-blue-600 text-white font-medium shadow-sm' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150">
                <i class="fa-solid fa-gauge-high w-5 text-center"></i>
                <span>Visão Geral</span>
            </button>
            <button @click="activeTab = 'connections'" :class="activeTab === 'connections' ? 'bg-blue-600 text-white font-medium shadow-sm' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150">
                <i class="fa-solid fa-network-wired w-5 text-center"></i>
                <span>Conexões Upstream</span>
                <span class="ml-auto text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/50" x-text="connections.length || 0"></span>
            </button>
            <button @click="activeTab = 'connection_models'" :class="activeTab === 'connection_models' ? 'bg-blue-600 text-white font-medium shadow-sm' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150">
                <i class="fa-solid fa-shapes w-5 text-center"></i>
                <span>Modelos de Conexão</span>
                <span class="ml-auto text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/50" x-text="connectionTemplates.length || 0"></span>
            </button>
            <button @click="activeTab = 'tools'" :class="activeTab === 'tools' ? 'bg-blue-600 text-white font-medium shadow-sm' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150">
                <i class="fa-solid fa-toolbox w-5 text-center"></i>
                <span>Catálogo de Tools</span>
                <span class="ml-auto text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/50" x-text="toolsTotal || overview.total_tools || 0"></span>
            </button>
            <button @click="activeTab = 'instances'" :class="activeTab === 'instances' ? 'bg-blue-600 text-white font-medium shadow-sm' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150">
                <i class="fa-solid fa-server w-5 text-center"></i>
                <span>Instâncias MCP</span>
                <span class="ml-auto text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/50" x-text="instances.length || 0"></span>
            </button>
            <button @click="activeTab = 'sources_map'" :class="activeTab === 'sources_map' ? 'bg-blue-600 text-white font-medium shadow-sm' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150">
                <i class="fa-solid fa-map-location-dot w-5 text-center"></i>
                <span>Data-Source Kits & Mapa</span>
            </button>
            <button @click="activeTab = 'users'" :class="activeTab === 'users' ? 'bg-blue-600 text-white font-medium shadow-sm' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150">
                <i class="fa-solid fa-users-gear w-5 text-center"></i>
                <span>Usuários & Sessões</span>
                <span class="ml-auto text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/50" x-text="usersList.length || 0"></span>
            </button>
            <button @click="activeTab = 'logs'" :class="activeTab === 'logs' ? 'bg-blue-600 text-white font-medium shadow-sm' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150">
                <i class="fa-solid fa-list-check w-5 text-center"></i>
                <span>Logs de Auditoria</span>
            </button>
        </nav>

        <!-- Status do Gateway no Rodapé -->
        <div class="p-4 border-t border-slate-800 bg-slate-950/20 text-xs">
            <div class="flex items-center justify-between mb-1.5">
                <span class="text-slate-400">Gateway Core:</span>
                <span class="inline-flex items-center gap-1.5 text-emerald-400 font-medium">
                    <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> Online
                </span>
            </div>
            <div class="text-slate-500 font-mono text-[11px] truncate">127.0.0.1:8000 &bull; mcpcentral</div>
        </div>
    </aside>

    <!-- Área Principal de Conteúdo -->
    <main class="flex-1 flex flex-col overflow-hidden bg-slate-100">
        <!-- Barra Superior -->
        <header class="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between shadow-xs">
            <div class="flex items-center gap-3">
                <h1 class="text-xl font-bold text-slate-800" x-text="pageTitles[activeTab]"></h1>
                <span class="text-xs px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-medium">Fase 3: Multi-Usuário & RBAC</span>
            </div>
            
            <div class="flex items-center gap-4">
                <!-- Seletor de Sessão Ativa / Usuário -->
                <div class="flex items-center gap-2.5 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200">
                    <div class="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs">
                        <span x-text="currentUser.username ? currentUser.username.substring(0, 2).toUpperCase() : 'EP'"></span>
                    </div>
                    <div class="text-left">
                        <div class="flex items-center gap-1.5">
                            <span class="text-xs font-bold text-slate-800" x-text="currentUser.display_name || currentUser.username || 'Carregando...'"></span>
                            <template x-if="currentUser.role === 'epy_root'">
                                <span class="px-1.5 py-0.2 rounded text-[10px] font-semibold bg-purple-100 text-purple-700 border border-purple-200">Master Admin</span>
                            </template>
                            <template x-if="currentUser.role !== 'epy_root'">
                                <span class="px-1.5 py-0.2 rounded text-[10px] font-semibold bg-slate-200 text-slate-700">Standard</span>
                            </template>
                        </div>
                    </div>
                    <button @click="showUserModal = true" class="ml-2 text-slate-400 hover:text-blue-600 text-xs px-1.5 py-1 rounded hover:bg-slate-200/60" title="Trocar Usuário ou Gerenciar Sessão">
                        <i class="fa-solid fa-arrows-rotate"></i>
                    </button>
                </div>

                <div class="h-6 w-px bg-slate-200"></div>

                <button @click="openTemplateModal()" class="inline-flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-lg text-white bg-blue-600 hover:bg-blue-700 shadow-xs transition-colors">
                    <i class="fa-solid fa-plus"></i>
                    <span>Nova Conexão</span>
                </button>
                <button @click="refreshAll()" class="inline-flex items-center gap-2 px-3.5 py-1.5 text-xs font-medium rounded-lg text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 shadow-xs transition-colors">
                    <i class="fa-solid fa-arrows-rotate" :class="loading ? 'animate-spin' : ''"></i>
                    <span>Atualizar</span>
                </button>
            </div>
        </header>

        <!-- Conteúdo Rolável -->
        <div class="flex-1 overflow-y-auto p-8">

            <!-- TAB 1: VISÃO GERAL (DASHBOARD) -->
            <div x-show="activeTab === 'dashboard'" class="space-y-6">
                <!-- Cards de Métricas (KPIs) -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-5">
                    <div class="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
                        <div class="flex items-center justify-between text-slate-500 mb-2">
                            <span class="text-xs font-semibold uppercase tracking-wider">Instâncias Ativas</span>
                            <div class="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center text-sm">
                                <i class="fa-solid fa-server"></i>
                            </div>
                        </div>
                        <div class="text-2xl font-bold text-slate-900" x-text="instances.length || overview.active_instances || 0"></div>
                        <div class="text-xs text-slate-500 mt-1">Endpoints independentes</div>
                    </div>
                    <div class="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
                        <div class="flex items-center justify-between text-slate-500 mb-2">
                            <span class="text-xs font-semibold uppercase tracking-wider">Conexões Upstream</span>
                            <div class="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center text-sm">
                                <i class="fa-solid fa-network-wired"></i>
                            </div>
                        </div>
                        <div class="text-2xl font-bold text-slate-900" x-text="connections.length || overview.total_connections || 0"></div>
                        <div class="text-xs text-slate-500 mt-1">Google Drive, Periskope, etc.</div>
                    </div>
                    <div class="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
                        <div class="flex items-center justify-between text-slate-500 mb-2">
                            <span class="text-xs font-semibold uppercase tracking-wider">Modelos de Conexão</span>
                            <div class="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center text-sm">
                                <i class="fa-solid fa-shapes"></i>
                            </div>
                        </div>
                        <div class="text-2xl font-bold text-slate-900" x-text="connectionTemplates.length || 0"></div>
                        <div class="text-xs text-slate-500 mt-1">Presets reutilizáveis salvos</div>
                    </div>
                    <div class="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
                        <div class="flex items-center justify-between text-slate-500 mb-2">
                            <span class="text-xs font-semibold uppercase tracking-wider">Data-Source Kits</span>
                            <div class="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center text-sm">
                                <i class="fa-solid fa-box-archive"></i>
                            </div>
                        </div>
                        <div class="text-2xl font-bold text-slate-900" x-text="dataSourceKits.length || 0"></div>
                        <div class="text-xs text-emerald-600 font-medium mt-1">Kits de fontes para agentes</div>
                    </div>
                </div>

                <!-- Painel de Governança e Escopos -->
                <div class="bg-gradient-to-r from-slate-900 to-indigo-950 rounded-2xl p-6 text-white shadow-md relative overflow-hidden">
                    <div class="relative z-10 max-w-2xl space-y-2">
                        <span class="text-xs font-bold uppercase tracking-wider text-blue-400 flex items-center gap-1.5">
                            <i class="fa-solid fa-shield-halved"></i> Governança de Escopo e Segurança
                        </span>
                        <h2 class="text-lg font-bold">Controle Estrito de Visibilidade: Privado, Compartilhado e Público</h2>
                        <p class="text-xs text-slate-300 leading-relaxed">
                            Conexões, instâncias e kits suportam segregação por usuário. Conforme política de conformidade, qualquer publicação no escopo <strong>Público</strong> é restrita exclusivamente ao <strong>Master Administrator</strong> (<code class="bg-slate-800 px-1.5 py-0.5 rounded text-blue-300 font-mono">epy_root</code>).
                        </p>
                    </div>
                </div>
            </div>

            <!-- TAB 2: CONEXÕES UPSTREAM -->
            <div x-show="activeTab === 'connections'" class="space-y-6">
                <!-- Filtros e Barra de Ação -->
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs">
                    <div class="flex items-center gap-2">
                        <button @click="connFilter = 'all'" :class="connFilter === 'all' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'" class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors">Todas</button>
                        <button @click="connFilter = 'private'" :class="connFilter === 'private' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'" class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5">
                            <i class="fa-solid fa-lock text-[10px]"></i> Privadas
                        </button>
                        <button @click="connFilter = 'shared'" :class="connFilter === 'shared' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'" class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5">
                            <i class="fa-solid fa-users text-[10px]"></i> Compartilhadas
                        </button>
                        <button @click="connFilter = 'public'" :class="connFilter === 'public' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'" class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5">
                            <i class="fa-solid fa-globe text-[10px]"></i> Públicas
                        </button>
                    </div>
                    <button @click="openTemplateModal()" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold flex items-center gap-2 shadow-xs transition-colors">
                        <i class="fa-solid fa-plus"></i> Adicionar Conexão
                    </button>
                </div>

                <!-- Grid de Conexões -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    <template x-for="conn in filteredConnections()" :key="conn.id">
                        <div class="bg-white rounded-xl border border-slate-200/80 shadow-xs p-5 space-y-4 hover:shadow-md transition-shadow flex flex-col justify-between">
                            <div class="space-y-3">
                                <div class="flex items-start justify-between">
                                    <div class="flex items-center gap-3">
                                        <div class="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center text-lg">
                                            <i :class="conn.type === 'stdio' ? 'fa-solid fa-terminal' : 'fa-solid fa-cloud'"></i>
                                        </div>
                                        <div>
                                            <h3 class="font-bold text-slate-900 text-sm" x-text="conn.name"></h3>
                                            <span class="text-xs font-mono text-slate-500" x-text="'prefix: ' + conn.prefix"></span>
                                        </div>
                                    </div>
                                    <span :class="getVisibilityBadgeClass(conn.visibility)" class="px-2 py-0.5 rounded-full text-[11px] font-semibold border flex items-center gap-1" x-html="getVisibilityBadgeHtml(conn.visibility)"></span>
                                </div>

                                <div class="space-y-1.5 text-xs text-slate-600 bg-slate-50 p-3 rounded-lg font-mono">
                                    <div class="flex justify-between">
                                        <span class="text-slate-400">Tipo:</span>
                                        <span class="font-bold text-slate-700" x-text="conn.type"></span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span class="text-slate-400">Ferramentas:</span>
                                        <span class="font-bold text-blue-600" x-text="(conn.tools_count || 0) + ' expostas'"></span>
                                    </div>
                                    <template x-if="conn.command">
                                        <div class="truncate text-slate-500">
                                            <span class="text-slate-400">Cmd:</span>
                                            <span x-text="conn.command + ' ' + (conn.args || []).join(' ')"></span>
                                        </div>
                                    </template>
                                </div>
                            </div>

                            <div class="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                                <button @click="openSaveAsTemplate(conn)" class="text-blue-600 hover:text-blue-800 text-xs font-semibold flex items-center gap-1.5" title="Salvar configuração como modelo reutilizável">
                                    <i class="fa-solid fa-bookmark"></i> Salvar como Modelo
                                </button>
                                <button @click="discoverTools(conn.id)" class="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-medium flex items-center gap-1">
                                    <i class="fa-solid fa-arrows-rotate"></i> Sincronizar
                                </button>
                            </div>
                        </div>
                    </template>
                </div>
            </div>

            <!-- TAB 3: MODELOS DE CONEXÃO (NOVA ABA) -->
            <div x-show="activeTab === 'connection_models'" class="space-y-6">
                <div class="flex items-center justify-between bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs">
                    <div>
                        <h2 class="text-base font-bold text-slate-900">Biblioteca de Modelos de Conexão</h2>
                        <p class="text-xs text-slate-500">Presets salvos para instanciar servidores MCP com parâmetros padronizados.</p>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
                    <template x-for="tmpl in connectionTemplates" :key="tmpl.id">
                        <div class="bg-white rounded-xl border border-slate-200/80 shadow-xs p-5 space-y-4 hover:shadow-md transition-shadow flex flex-col justify-between">
                            <div class="space-y-3">
                                <div class="flex items-start justify-between">
                                    <div>
                                        <h3 class="font-bold text-slate-900 text-sm" x-text="tmpl.name"></h3>
                                        <p class="text-xs text-slate-500 mt-0.5" x-text="tmpl.description || 'Sem descrição'"></p>
                                    </div>
                                    <span :class="getVisibilityBadgeClass(tmpl.visibility)" class="px-2 py-0.5 rounded-full text-[11px] font-semibold border flex items-center gap-1" x-html="getVisibilityBadgeHtml(tmpl.visibility)"></span>
                                </div>

                                <div class="bg-slate-50 p-3 rounded-lg text-xs font-mono space-y-1 text-slate-600">
                                    <div><span class="text-slate-400">Prefixo:</span> <strong x-text="tmpl.prefix"></strong></div>
                                    <div class="truncate"><span class="text-slate-400">Cmd:</span> <span x-text="tmpl.command + ' ' + (tmpl.args || []).join(' ')"></span></div>
                                </div>
                            </div>

                            <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
                                <button @click="deleteConnectionTemplate(tmpl.id)" class="text-rose-500 hover:text-rose-700 text-xs font-medium">
                                    <i class="fa-solid fa-trash"></i> Excluir
                                </button>
                                <button @click="openInstantiateModal(tmpl)" class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5">
                                    <i class="fa-solid fa-bolt"></i> Instanciar Conexão
                                </button>
                            </div>
                        </div>
                    </template>
                </div>
            </div>

            <!-- TAB 4: CATÁLOGO DE TOOLS -->
            <div x-show="activeTab === 'tools'" class="space-y-6">
                <div class="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex flex-col md:flex-row gap-4 items-center justify-between">
                    <div class="w-full md:w-96 relative">
                        <i class="fa-solid fa-magnifying-glass absolute left-3 top-2.5 text-slate-400 text-xs"></i>
                        <input type="text" x-model="toolSearch" @input.debounce.300ms="fetchTools()" placeholder="Pesquisar ferramentas por nome ou descrição..." class="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                    </div>
                </div>

                <div class="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
                    <table class="w-full text-left border-collapse text-xs">
                        <thead>
                            <tr class="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                                <th class="p-3.5">Ferramenta</th>
                                <th class="p-3.5">Conexão Upstream</th>
                                <th class="p-3.5">Descrição</th>
                                <th class="p-3.5 text-right">Ação</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <template x-for="t in toolsList" :key="t.id">
                                <tr class="hover:bg-slate-50/80">
                                    <td class="p-3.5 font-mono font-bold text-blue-600" x-text="t.namespaced_name"></td>
                                    <td class="p-3.5 font-mono text-slate-500" x-text="t.connection_id"></td>
                                    <td class="p-3.5 text-slate-600 max-w-md truncate" x-text="t.description || '-'"></td>
                                    <td class="p-3.5 text-right">
                                        <button @click="inspectTool(t)" class="text-blue-600 hover:text-blue-800 font-medium">Ver Schema</button>
                                    </td>
                                </tr>
                            </template>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- TAB 5: INSTÂNCIAS MCP -->
            <div x-show="activeTab === 'instances'" class="space-y-6">
                <div class="flex items-center justify-between">
                    <div>
                        <h2 class="text-base font-bold text-slate-900">Endpoints MCP dos Agentes</h2>
                        <p class="text-xs text-slate-500">Cada instância agrega conexões e expõe um endpoint SSE autenticado para o Paperclip.</p>
                    </div>
                </div>

                <div class="space-y-5">
                    <template x-for="inst in instances" :key="inst.id">
                        <div class="bg-white rounded-xl border border-slate-200/80 shadow-xs p-6 space-y-5">
                            <div class="flex items-start justify-between border-b border-slate-100 pb-4">
                                <div>
                                    <div class="flex items-center gap-3">
                                        <h3 class="font-bold text-slate-900 text-base" x-text="inst.name"></h3>
                                        <span class="text-xs font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200" x-text="inst.slug"></span>
                                        <span :class="getVisibilityBadgeClass(inst.visibility)" class="px-2 py-0.5 rounded-full text-[11px] font-semibold border flex items-center gap-1" x-html="getVisibilityBadgeHtml(inst.visibility)"></span>
                                    </div>
                                    <p class="text-xs text-slate-500 mt-1" x-text="inst.description || 'Instância operacional MCP'"></p>
                                </div>
                                <div class="flex items-center gap-2">
                                    <button @click="openSaveAsKit(inst)" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs">
                                        <i class="fa-solid fa-box-archive"></i> Salvar como Kit
                                    </button>
                                    <button @click="reloadInstance(inst.slug)" class="px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg text-xs font-semibold flex items-center gap-1.5">
                                        <i class="fa-solid fa-arrows-rotate"></i> Recarregar
                                    </button>
                                </div>
                            </div>

                            <!-- Tokens e Endpoint -->
                            <div class="bg-slate-50 rounded-lg p-4 border border-slate-200 space-y-3">
                                <span class="text-xs font-bold text-slate-700 uppercase tracking-wider block">Conexão SSE para Agentes (Paperclip / Codex / Claude):</span>
                                <template x-for="t in inst.tokens" :key="t.id">
                                    <div class="flex items-center justify-between bg-white p-2.5 rounded border border-slate-200 text-xs">
                                        <div class="flex items-center gap-3 truncate">
                                            <i class="fa-solid fa-key text-amber-500"></i>
                                            <span class="font-medium text-slate-800" x-text="t.label"></span>
                                            <code class="font-mono bg-slate-100 px-2 py-0.5 rounded text-slate-700" x-text="t.token"></code>
                                        </div>
                                        <button @click="copyToClipboard(getEndpointUrl(inst.slug, t.token))" class="text-blue-600 hover:text-blue-800 font-semibold text-xs flex items-center gap-1 flex-shrink-0">
                                            <i class="fa-regular fa-copy"></i> Copiar URL SSE
                                        </button>
                                    </div>
                                </template>
                            </div>
                        </div>
                    </template>
                </div>
            </div>

            <!-- TAB 6: DATA-SOURCE KITS & MAPA DE FONTES -->
            <div x-show="activeTab === 'sources_map'" class="space-y-6">
                <!-- Seletor de Sub-Abas -->
                <div class="flex items-center justify-between border-b border-slate-200 pb-3">
                    <div class="flex items-center gap-3">
                        <button @click="sourcesTab = 'active_instance'" :class="sourcesTab === 'active_instance' ? 'bg-blue-600 text-white font-semibold' : 'bg-white text-slate-600 hover:bg-slate-100'" class="px-4 py-2 rounded-lg text-xs shadow-xs transition-colors flex items-center gap-2">
                            <i class="fa-solid fa-map-location-dot"></i> Mapa da Instância Ativa
                        </button>
                        <button @click="sourcesTab = 'kits_library'" :class="sourcesTab === 'kits_library' ? 'bg-blue-600 text-white font-semibold' : 'bg-white text-slate-600 hover:bg-slate-100'" class="px-4 py-2 rounded-lg text-xs shadow-xs transition-colors flex items-center gap-2">
                            <i class="fa-solid fa-boxes-stacked"></i> Biblioteca de Kits (<span x-text="dataSourceKits.length"></span>)
                        </button>
                    </div>

                    <template x-if="sourcesTab === 'active_instance'">
                        <button @click="saveSourcesMap()" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-2 transition-colors">
                            <i class="fa-solid fa-floppy-disk"></i> Salvar Mapa de Fontes
                        </button>
                    </template>
                </div>

                <!-- Sub-Aba 1: Mapa da Instância -->
                <div x-show="sourcesTab === 'active_instance'" class="bg-white rounded-xl border border-slate-200/80 shadow-xs p-6 space-y-6">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div>
                            <h3 class="text-sm font-bold text-slate-800">Diretrizes da Instância (Horst Group)</h3>
                            <p class="text-xs text-slate-500">Consultadas pelos agentes através de <code class="font-mono text-blue-600">central__get_data_sources_map</code>.</p>
                        </div>
                        <button @click="addSourceItem()" class="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1">
                            <i class="fa-solid fa-plus"></i> Adicionar Fonte
                        </button>
                    </div>

                    <div class="space-y-4">
                        <template x-for="(src, idx) in sourcesMapData.sources" :key="idx">
                            <div class="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-3 relative">
                                <button @click="removeSourceItem(idx)" class="absolute right-3 top-3 text-slate-400 hover:text-rose-600"><i class="fa-solid fa-trash text-xs"></i></button>
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    <div>
                                        <label class="block text-[11px] font-semibold text-slate-600 mb-1">Nome da Fonte</label>
                                        <input type="text" x-model="src.name" class="w-full bg-white border border-slate-300 rounded px-2.5 py-1.5 text-xs text-slate-800 font-medium">
                                    </div>
                                    <div>
                                        <label class="block text-[11px] font-semibold text-slate-600 mb-1">Sistema (Slug)</label>
                                        <input type="text" x-model="src.system" class="w-full bg-white border border-slate-300 rounded px-2.5 py-1.5 text-xs text-slate-800 font-mono">
                                    </div>
                                </div>
                                <div>
                                    <label class="block text-[11px] font-semibold text-slate-600 mb-1">Diretriz Operacional para os Agentes</label>
                                    <textarea x-model="src.guidance" rows="2" class="w-full bg-white border border-slate-300 rounded px-2.5 py-1.5 text-xs text-slate-800"></textarea>
                                </div>
                            </div>
                        </template>
                    </div>
                </div>

                <!-- Sub-Aba 2: Biblioteca de Kits -->
                <div x-show="sourcesTab === 'kits_library'" class="space-y-4">
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
                        <template x-for="kit in dataSourceKits" :key="kit.id">
                            <div class="bg-white rounded-xl border border-slate-200/80 shadow-xs p-5 space-y-4 hover:shadow-md transition-shadow flex flex-col justify-between">
                                <div class="space-y-2">
                                    <div class="flex items-start justify-between">
                                        <h3 class="font-bold text-slate-900 text-sm" x-text="kit.name"></h3>
                                        <span :class="getVisibilityBadgeClass(kit.visibility)" class="px-2 py-0.5 rounded-full text-[11px] font-semibold border flex items-center gap-1" x-html="getVisibilityBadgeHtml(kit.visibility)"></span>
                                    </div>
                                    <span class="inline-block px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-slate-100 text-slate-600" x-text="kit.category"></span>
                                    <p class="text-xs text-slate-500" x-text="kit.description"></p>
                                    <div class="text-xs text-blue-600 font-semibold" x-text="(kit.sources_count || (kit.sources || []).length) + ' fontes empacotadas'"></div>
                                </div>

                                <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
                                    <button @click="deleteKit(kit.id)" class="text-rose-500 hover:text-rose-700 text-xs font-medium">
                                        <i class="fa-solid fa-trash"></i> Excluir
                                    </button>
                                    <button @click="applyKitToInstance(kit.id, 'horst-suite')" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5">
                                        <i class="fa-solid fa-file-import"></i> Aplicar à Instância
                                    </button>
                                </div>
                            </div>
                        </template>
                    </div>
                </div>
            </div>

            <!-- TAB 7: USUÁRIOS & SESSÕES -->
            <div x-show="activeTab === 'users'" class="space-y-6">
                <div class="flex items-center justify-between bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs">
                    <div>
                        <h2 class="text-base font-bold text-slate-900">Usuários e Controle de Acesso</h2>
                        <p class="text-xs text-slate-500">Gerenciamento de contas registradas e alternância rápida de sessão.</p>
                    </div>
                    <template x-if="currentUser.role === 'epy_root'">
                        <button @click="showCreateUserModal = true" class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5">
                            <i class="fa-solid fa-user-plus"></i> Novo Usuário
                        </button>
                    </template>
                </div>

                <div class="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
                    <table class="w-full text-left border-collapse text-xs">
                        <thead>
                            <tr class="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                                <th class="p-3.5">Usuário</th>
                                <th class="p-3.5">Nome de Exibição</th>
                                <th class="p-3.5">Nível de Acesso (Role)</th>
                                <th class="p-3.5">Data de Criação</th>
                                <th class="p-3.5 text-right">Ação</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <template x-for="u in usersList" :key="u.id">
                                <tr class="hover:bg-slate-50/80">
                                    <td class="p-3.5 font-bold font-mono text-slate-900" x-text="u.username"></td>
                                    <td class="p-3.5 text-slate-700" x-text="u.display_name || u.username"></td>
                                    <td class="p-3.5">
                                        <template x-if="u.role === 'epy_root'">
                                            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-700 border border-purple-200">Master Admin</span>
                                        </template>
                                        <template x-if="u.role !== 'epy_root'">
                                            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">Standard User</span>
                                        </template>
                                    </td>
                                    <td class="p-3.5 text-slate-500" x-text="formatDate(u.created_at)"></td>
                                    <td class="p-3.5 text-right">
                                        <button @click="switchUserAccount(u.username)" class="text-blue-600 hover:text-blue-800 font-semibold">Alternar Sessão</button>
                                    </td>
                                </tr>
                            </template>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- TAB 8: LOGS DE AUDITORIA -->
            <div x-show="activeTab === 'logs'" class="space-y-6">
                <div class="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
                    <table class="w-full text-left border-collapse text-xs">
                        <thead>
                            <tr class="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                                <th class="p-3.5">Horário</th>
                                <th class="p-3.5">Instância</th>
                                <th class="p-3.5">Ferramenta Executada</th>
                                <th class="p-3.5">Status</th>
                                <th class="p-3.5">Tempo</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <template x-for="log in recentLogs" :key="log.id">
                                <tr>
                                    <td class="p-3.5 text-slate-500 font-mono" x-text="formatDate(log.created_at)"></td>
                                    <td class="p-3.5 font-mono text-slate-700" x-text="log.instance_slug"></td>
                                    <td class="p-3.5 font-mono font-bold text-slate-900" x-text="log.tool_name"></td>
                                    <td class="p-3.5">
                                        <span :class="log.status === 'success' ? 'text-emerald-700 bg-emerald-50 border-emerald-200' : 'text-rose-700 bg-rose-50 border-rose-200'" class="px-2 py-0.5 rounded border text-[10px] font-bold uppercase" x-text="log.status"></span>
                                    </td>
                                    <td class="p-3.5 font-mono text-slate-500" x-text="log.execution_time_ms + 'ms'"></td>
                                </tr>
                            </template>
                        </tbody>
                    </table>
                </div>
            </div>

        </div>
    </main>

    <!-- Modais do Sistema -->

    <!-- Modal: Alternar Sessão / Login -->
    <div x-show="showUserModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-xs p-4" @click.self="showUserModal = false">
        <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 space-y-4 border border-slate-200">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="font-bold text-slate-900 text-base">Alternar Sessão / Usuário</h3>
                <button @click="showUserModal = false" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <p class="text-xs text-slate-500">Selecione uma conta ativa ou crie uma nova sessão rápida para testar os níveis de visibilidade.</p>
            <div class="space-y-2">
                <template x-for="u in usersList" :key="u.id">
                    <div @click="switchUserAccount(u.username)" class="p-3 rounded-lg border border-slate-200 hover:border-blue-500 hover:bg-blue-50/30 cursor-pointer flex items-center justify-between transition-colors">
                        <div>
                            <span class="font-bold text-xs text-slate-900" x-text="u.display_name || u.username"></span>
                            <span class="text-[11px] text-slate-400 block font-mono" x-text="'@' + u.username"></span>
                        </div>
                        <span :class="u.role === 'epy_root' ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-600'" class="px-2 py-0.5 rounded text-[10px] font-semibold" x-text="u.role"></span>
                    </div>
                </template>
            </div>
        </div>
    </div>

    <!-- Modal: Salvar Conexão como Modelo -->
    <div x-show="showSaveAsTemplateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4" @click.self="showSaveAsTemplateModal = false">
        <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 space-y-4 border border-slate-200">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="font-bold text-slate-900 text-base">Salvar como Modelo de Conexão</h3>
                <button @click="showSaveAsTemplateModal = false" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Nome do Modelo</label>
                    <input type="text" x-model="newTemplateName" class="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Descrição</label>
                    <textarea x-model="newTemplateDesc" rows="2" class="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs"></textarea>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Nível de Visibilidade</label>
                    <select x-model="newTemplateVisibility" class="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs">
                        <option value="private">🔒 Privado (Apenas eu)</option>
                        <option value="shared">👥 Compartilhado (Equipe)</option>
                        <option value="public" :disabled="!currentUser.is_master_admin">🌐 Público (Global - Requer Master Admin)</option>
                    </select>
                </div>
            </div>
            <div class="pt-3 border-t border-slate-100 flex justify-end gap-2">
                <button @click="showSaveAsTemplateModal = false" class="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-lg">Cancelar</button>
                <button @click="submitSaveAsTemplate()" class="px-4 py-2 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-xs">Salvar Modelo</button>
            </div>
        </div>
    </div>

    <!-- Modal: Instanciar Modelo de Conexão -->
    <div x-show="showInstantiateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4" @click.self="showInstantiateModal = false">
        <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 space-y-4 border border-slate-200">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="font-bold text-slate-900 text-base">Instanciar Nova Conexão via Modelo</h3>
                <button @click="showInstantiateModal = false" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Identificador da Conexão (ID único)</label>
                    <input type="text" x-model="instantiateForm.connection_id" class="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs font-mono">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Nome de Exibição</label>
                    <input type="text" x-model="instantiateForm.name" class="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Prefixo das Tools</label>
                    <input type="text" x-model="instantiateForm.prefix" class="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs font-mono">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Visibilidade</label>
                    <select x-model="instantiateForm.visibility" class="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs">
                        <option value="private">🔒 Privado (Apenas eu)</option>
                        <option value="shared">👥 Compartilhado (Equipe)</option>
                        <option value="public" :disabled="!currentUser.is_master_admin">🌐 Público (Global - Requer Master Admin)</option>
                    </select>
                </div>
            </div>
            <div class="pt-3 border-t border-slate-100 flex justify-end gap-2">
                <button @click="showInstantiateModal = false" class="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-lg">Cancelar</button>
                <button @click="submitInstantiateTemplate()" class="px-4 py-2 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-xs">Criar Conexão</button>
            </div>
        </div>
    </div>

    <!-- Modal: Salvar Instância como Kit de Fontes -->
    <div x-show="showSaveAsKitModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4" @click.self="showSaveAsKitModal = false">
        <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 space-y-4 border border-slate-200">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="font-bold text-slate-900 text-base">Salvar como Data-Source Kit</h3>
                <button @click="showSaveAsKitModal = false" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Nome do Kit</label>
                    <input type="text" x-model="newKitName" class="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Categoria</label>
                    <input type="text" x-model="newKitCategory" placeholder="ex: Operações, Financeiro" class="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Descrição</label>
                    <textarea x-model="newKitDesc" rows="2" class="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs"></textarea>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Nível de Visibilidade</label>
                    <select x-model="newKitVisibility" class="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs">
                        <option value="private">🔒 Privado (Apenas eu)</option>
                        <option value="shared">👥 Compartilhado (Equipe)</option>
                        <option value="public" :disabled="!currentUser.is_master_admin">🌐 Público (Global - Requer Master Admin)</option>
                    </select>
                </div>
            </div>
            <div class="pt-3 border-t border-slate-100 flex justify-end gap-2">
                <button @click="showSaveAsKitModal = false" class="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-lg">Cancelar</button>
                <button @click="submitSaveAsKit()" class="px-4 py-2 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg shadow-xs">Salvar Kit</button>
            </div>
        </div>
    </div>

    <!-- Modal: Autenticação Master Admin -->
    <div x-show="showAuthModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-xs p-4">
        <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 space-y-4 border border-slate-200">
            <div class="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center text-xl mx-auto">
                <i class="fa-solid fa-shield-halved"></i>
            </div>
            <div class="text-center">
                <h3 class="font-bold text-slate-900 text-lg">Central Admin Protegido</h3>
                <p class="text-xs text-slate-500 mt-1">Informe a chave mestre administrativa (CENTRAL_ADMIN_KEY) para autenticar a sessão.</p>
            </div>
            <div x-show="authErrorMessage" class="p-2.5 rounded bg-rose-50 border border-rose-200 text-rose-700 text-xs text-center" x-text="authErrorMessage"></div>
            <div class="space-y-3">
                <input type="password" x-model="authKeyInput" @keydown.enter="saveAdminKey()" placeholder="Insira sua CENTRAL_ADMIN_KEY..." class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:ring-2 focus:ring-blue-500">
                <button @click="saveAdminKey()" class="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs">Autenticar e Entrar</button>
            </div>
        </div>
    </div>

    <!-- Modal: Adicionar via Template Pré-definido -->
    <div x-show="showTemplateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4" @click.self="showTemplateModal = false">
        <div class="bg-white rounded-xl shadow-2xl max-w-3xl w-full p-6 space-y-5 max-h-[90vh] flex flex-col">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                    <h3 class="font-bold text-slate-900 text-lg">Adicionar Nova Conexão por Template</h3>
                    <p class="text-xs text-slate-500">Selecione um template pronto para inicializar o servidor MCP.</p>
                </div>
                <button @click="showTemplateModal = false" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark text-lg"></i></button>
            </div>

            <div x-show="!selectedTemplate" class="grid grid-cols-1 md:grid-cols-2 gap-4 overflow-y-auto p-1">
                <template x-for="tmpl in templates" :key="tmpl.id">
                    <div @click="selectTemplate(tmpl)" class="p-4 rounded-xl border border-slate-200 hover:border-blue-500 hover:shadow-xs transition-all cursor-pointer flex gap-3.5 items-start bg-slate-50/50 hover:bg-blue-50/20">
                        <div class="w-10 h-10 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center text-lg flex-shrink-0">
                            <i :class="tmpl.icon"></i>
                        </div>
                        <div>
                            <div class="flex items-center gap-2">
                                <h4 class="font-bold text-slate-900 text-sm" x-text="tmpl.name"></h4>
                                <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-200/60 text-slate-600 uppercase" x-text="tmpl.type"></span>
                            </div>
                            <p class="text-xs text-slate-500 mt-1" x-text="tmpl.description"></p>
                        </div>
                    </div>
                </template>
            </div>

            <div x-show="selectedTemplate" class="space-y-4 overflow-y-auto p-1">
                <div class="flex items-center justify-between bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-800">
                    <div class="flex items-center gap-2">
                        <i :class="selectedTemplate?.icon"></i>
                        <span class="font-bold" x-text="selectedTemplate?.name"></span>
                    </div>
                    <button @click="selectedTemplate = null" class="text-blue-600 hover:underline">Trocar template</button>
                </div>

                <div class="space-y-3">
                    <template x-for="field in selectedTemplate?.form_fields" :key="field.name">
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">
                                <span x-text="field.label"></span>
                                <span x-show="field.required" class="text-rose-500">*</span>
                            </label>
                            
                            <template x-if="field.type === 'textarea'">
                                <textarea x-model="templateFormValues[field.name]" :placeholder="field.placeholder" rows="3" class="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs font-mono"></textarea>
                            </template>
                            <template x-if="field.type === 'boolean'">
                                <label class="inline-flex items-center gap-2 cursor-pointer">
                                    <input type="checkbox" x-model="templateFormValues[field.name]" class="rounded text-blue-600 focus:ring-blue-500">
                                    <span class="text-xs text-slate-600" x-text="field.label"></span>
                                </label>
                            </template>
                            <template x-if="field.type === 'password'">
                                <input type="password" x-model="templateFormValues[field.name]" :placeholder="field.placeholder" class="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs">
                            </template>
                            <template x-if="field.type === 'text'">
                                <input type="text" x-model="templateFormValues[field.name]" :placeholder="field.placeholder" class="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs">
                            </template>
                        </div>
                    </template>
                </div>
            </div>

            <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
                <button @click="showTemplateModal = false" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium">Cancelar</button>
                <button x-show="selectedTemplate" @click="submitTemplateForm()" class="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs">Criar Conexão</button>
            </div>
        </div>
    </div>

    <!-- Script Alpine.js do Aplicativo -->
    <script>
        function centralApp() {
            return {
                activeTab: 'dashboard',
                sourcesTab: 'active_instance',
                connFilter: 'all',
                loading: false,
                adminKey: localStorage.getItem('central_admin_key') || '',
                sessionToken: localStorage.getItem('central_session_token') || '',
                showAuthModal: false,
                showUserModal: false,
                authKeyInput: '',
                authErrorMessage: '',
                currentUser: { username: '', role: 'standard', is_master_admin: false },
                usersList: [],
                overview: {},
                connections: [],
                connectionTemplates: [],
                dataSourceKits: [],
                instances: [],
                toolsList: [],
                toolsTotal: 0,
                recentLogs: [],
                templates: [],
                toolSearch: '',
                activeModalTool: null,
                showTemplateModal: false,
                selectedTemplate: null,
                templateFormValues: {},
                showSaveAsTemplateModal: false,
                saveTemplateTargetConn: null,
                newTemplateName: '',
                newTemplateDesc: '',
                newTemplateVisibility: 'shared',
                showInstantiateModal: false,
                instantiateTargetTmpl: null,
                instantiateForm: { connection_id: '', name: '', prefix: '', visibility: 'shared' },
                showSaveAsKitModal: false,
                saveKitTargetInstance: null,
                newKitName: '',
                newKitCategory: 'Operações',
                newKitDesc: '',
                newKitVisibility: 'shared',
                sourcesMapData: { organization: 'Horst Group', sources: [] },
                pageTitles: {
                    dashboard: 'Visão Geral do Central',
                    connections: 'Conexões Upstream & Provedores',
                    connection_models: 'Modelos de Conexão Salvos',
                    tools: 'Catálogo de Tools Agregadas',
                    instances: 'Instâncias & Endpoints MCP',
                    sources_map: 'Data-Source Kits & Mapa Operacional',
                    users: 'Gestão de Usuários & Sessões',
                    logs: 'Auditoria de Execução'
                },
                async apiFetch(url, options = {}) {
                    options.headers = options.headers || {};
                    if (this.adminKey) {
                        options.headers['X-Central-Admin-Key'] = this.adminKey;
                    }
                    if (this.sessionToken) {
                        options.headers['X-Central-Session-Token'] = this.sessionToken;
                    }
                    try {
                        const res = await fetch(url, options);
                        if (res.status === 401) {
                            this.showAuthModal = true;
                            this.authErrorMessage = 'Sessão expirada ou chave administrativa ausente.';
                        }
                        return res;
                    } catch (e) {
                        console.error('Fetch error:', e);
                        throw e;
                    }
                },
                saveAdminKey() {
                    const k = (this.authKeyInput || '').trim();
                    if (k) {
                        this.adminKey = k;
                        localStorage.setItem('central_admin_key', k);
                        this.showAuthModal = false;
                        this.authErrorMessage = '';
                        this.refreshAll();
                    }
                },
                async initApp() {
                    const params = new URLSearchParams(window.location.search);
                    const qKey = params.get('admin_key');
                    if (qKey) {
                        this.adminKey = qKey.trim();
                        localStorage.setItem('central_admin_key', this.adminKey);
                    }
                    if (!this.adminKey && !this.sessionToken) {
                        this.showAuthModal = true;
                        return;
                    }
                    await this.fetchMe();
                    await this.refreshAll();
                },
                async fetchMe() {
                    try {
                        const res = await this.apiFetch('/api/v1/auth/me');
                        if (res && res.ok) {
                            this.currentUser = await res.json();
                        }
                    } catch (e) {
                        console.warn('Erro ao carregar perfil:', e);
                    }
                },
                async refreshAll() {
                    this.loading = true;
                    try {
                        await Promise.all([
                            this.fetchMe(),
                            this.fetchOverview(),
                            this.fetchConnections(),
                            this.fetchConnectionTemplates(),
                            this.fetchDataSourceKits(),
                            this.fetchInstances(),
                            this.fetchTools(),
                            this.fetchUsers(),
                            this.fetchLogs(),
                            this.fetchTemplates(),
                            this.fetchSourcesMap(),
                        ]);
                    } finally {
                        this.loading = false;
                    }
                },
                async fetchOverview() {
                    const res = await this.apiFetch('/api/v1/overview');
                    if (res && res.ok) this.overview = await res.json();
                },
                async fetchConnections() {
                    const res = await this.apiFetch('/api/v1/connections');
                    if (res && res.ok) this.connections = await res.json();
                },
                async fetchConnectionTemplates() {
                    const res = await this.apiFetch('/api/v1/connection-templates');
                    if (res && res.ok) this.connectionTemplates = await res.json();
                },
                async fetchDataSourceKits() {
                    const res = await this.apiFetch('/api/v1/data-source-kits');
                    if (res && res.ok) this.dataSourceKits = await res.json();
                },
                async fetchInstances() {
                    const res = await this.apiFetch('/api/v1/instances');
                    if (res && res.ok) this.instances = await res.json();
                },
                async fetchUsers() {
                    const res = await this.apiFetch('/api/v1/users');
                    if (res && res.ok) this.usersList = await res.json();
                },
                async fetchTools() {
                    let url = `/api/v1/tools?limit=150`;
                    if (this.toolSearch) url += `&query=${encodeURIComponent(this.toolSearch)}`;
                    const res = await this.apiFetch(url);
                    if (res && res.ok) {
                        const data = await res.json();
                        this.toolsList = data.items;
                        this.toolsTotal = data.total;
                    }
                },
                async fetchLogs() {
                    const res = await this.apiFetch('/api/v1/logs?limit=50');
                    if (res && res.ok) this.recentLogs = await res.json();
                },
                async fetchTemplates() {
                    const res = await this.apiFetch('/api/v1/templates');
                    if (res && res.ok) this.templates = await res.json();
                },
                async fetchSourcesMap() {
                    const res = await this.apiFetch('/api/v1/instances/horst-suite/sources-map');
                    if (res && res.ok) this.sourcesMapData = await res.json();
                },
                async switchUserAccount(username) {
                    try {
                        const res = await this.apiFetch('/api/v1/auth/switch-user', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ username })
                        });
                        if (res && res.ok) {
                            const data = await res.json();
                            this.sessionToken = data.token;
                            localStorage.setItem('central_session_token', data.token);
                            this.currentUser = data.user;
                            this.currentUser.is_master_admin = data.user.role === 'epy_root';
                            this.showUserModal = false;
                            await this.refreshAll();
                        }
                    } catch (e) {
                        alert('Erro ao alternar usuário: ' + e);
                    }
                },
                openSaveAsTemplate(conn) {
                    this.saveTemplateTargetConn = conn;
                    this.newTemplateName = `Modelo - ${conn.name}`;
                    this.newTemplateDesc = `Preset exportado da conexão ${conn.name}`;
                    this.newTemplateVisibility = conn.visibility === 'public' && !this.currentUser.is_master_admin ? 'shared' : (conn.visibility || 'shared');
                    this.showSaveAsTemplateModal = true;
                },
                async submitSaveAsTemplate() {
                    if (!this.saveTemplateTargetConn) return;
                    try {
                        const res = await this.apiFetch(`/api/v1/connections/${this.saveTemplateTargetConn.id}/save-as-template`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                name: this.newTemplateName,
                                description: this.newTemplateDesc,
                                visibility: this.newTemplateVisibility
                            })
                        });
                        const data = await res.json();
                        if (res.ok) {
                            alert(`Modelo '${data.name}' salvo com sucesso!`);
                            this.showSaveAsTemplateModal = false;
                            await this.fetchConnectionTemplates();
                        } else {
                            alert('Erro: ' + (data.detail || 'Falha ao salvar modelo'));
                        }
                    } catch (e) {
                        alert('Erro: ' + e);
                    }
                },
                openInstantiateModal(tmpl) {
                    this.instantiateTargetTmpl = tmpl;
                    this.instantiateForm = {
                        connection_id: `${tmpl.prefix}_${Math.floor(Math.random() * 1000)}`,
                        name: `${tmpl.name} (Instância)`,
                        prefix: tmpl.prefix,
                        visibility: tmpl.visibility === 'public' && !this.currentUser.is_master_admin ? 'shared' : (tmpl.visibility || 'shared')
                    };
                    this.showInstantiateModal = true;
                },
                async submitInstantiateTemplate() {
                    if (!this.instantiateTargetTmpl) return;
                    try {
                        const res = await this.apiFetch(`/api/v1/connection-templates/${this.instantiateTargetTmpl.id}/instantiate`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(this.instantiateForm)
                        });
                        const data = await res.json();
                        if (res.ok) {
                            alert(`Conexão '${data.connection_id}' instanciada e ativada com sucesso!`);
                            this.showInstantiateModal = false;
                            await this.fetchConnections();
                            this.activeTab = 'connections';
                        } else {
                            alert('Erro: ' + (data.detail || 'Falha ao instanciar'));
                        }
                    } catch (e) {
                        alert('Erro: ' + e);
                    }
                },
                async deleteConnectionTemplate(tmplId) {
                    if (!confirm('Deseja realmente remover este modelo de conexão?')) return;
                    try {
                        const res = await this.apiFetch(`/api/v1/connection-templates/${tmplId}`, { method: 'DELETE' });
                        if (res.ok) {
                            await this.fetchConnectionTemplates();
                        } else {
                            const err = await res.json();
                            alert('Erro: ' + (err.detail || 'Falha ao excluir'));
                        }
                    } catch (e) {
                        alert('Erro: ' + e);
                    }
                },
                openSaveAsKit(inst) {
                    this.saveKitTargetInstance = inst;
                    this.newKitName = `Kit de Fontes - ${inst.name}`;
                    this.newKitCategory = 'Operações';
                    this.newKitDesc = `Empacotamento das diretrizes da instância ${inst.name}`;
                    this.newKitVisibility = 'shared';
                    this.showSaveAsKitModal = true;
                },
                async submitSaveAsKit() {
                    if (!this.saveKitTargetInstance) return;
                    try {
                        const res = await this.apiFetch(`/api/v1/instances/${this.saveKitTargetInstance.slug}/save-as-kit`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                name: this.newKitName,
                                category: this.newKitCategory,
                                description: this.newKitDesc,
                                visibility: this.newKitVisibility
                            })
                        });
                        const data = await res.json();
                        if (res.ok) {
                            alert(`Kit '${data.name}' salvo com sucesso!`);
                            this.showSaveAsKitModal = false;
                            await this.fetchDataSourceKits();
                        } else {
                            alert('Erro: ' + (data.detail || 'Falha ao salvar kit'));
                        }
                    } catch (e) {
                        alert('Erro: ' + e);
                    }
                },
                async applyKitToInstance(kitId, instanceSlug) {
                    if (!confirm(`Aplicar este Kit ao Mapa de Fontes da instância '${instanceSlug}'?`)) return;
                    try {
                        const res = await this.apiFetch(`/api/v1/data-source-kits/${kitId}/apply-to-instance/${instanceSlug}`, {
                            method: 'POST'
                        });
                        const data = await res.json();
                        if (res.ok) {
                            alert(`Kit aplicado com sucesso! ${data.sources_count} fontes ativas.`);
                            await this.fetchSourcesMap();
                            this.sourcesTab = 'active_instance';
                        } else {
                            alert('Erro: ' + (data.detail || 'Falha ao aplicar kit'));
                        }
                    } catch (e) {
                        alert('Erro: ' + e);
                    }
                },
                async deleteKit(kitId) {
                    if (!confirm('Deseja realmente excluir este Kit de Data-Sources?')) return;
                    try {
                        const res = await this.apiFetch(`/api/v1/data-source-kits/${kitId}`, { method: 'DELETE' });
                        if (res.ok) {
                            await this.fetchDataSourceKits();
                        } else {
                            const err = await res.json();
                            alert('Erro: ' + (err.detail || 'Falha ao excluir'));
                        }
                    } catch (e) {
                        alert('Erro: ' + e);
                    }
                },
                filteredConnections() {
                    if (this.connFilter === 'all') return this.connections;
                    return this.connections.filter(c => (c.visibility || 'shared') === this.connFilter);
                },
                getVisibilityBadgeClass(vis) {
                    if (vis === 'public') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
                    if (vis === 'private') return 'bg-slate-100 text-slate-700 border-slate-300';
                    return 'bg-blue-50 text-blue-700 border-blue-200';
                },
                getVisibilityBadgeHtml(vis) {
                    if (vis === 'public') return '<i class="fa-solid fa-globe text-[10px]"></i> Público';
                    if (vis === 'private') return '<i class="fa-solid fa-lock text-[10px]"></i> Privado';
                    return '<i class="fa-solid fa-users text-[10px]"></i> Compartilhado';
                },
                openTemplateModal() {
                    this.selectedTemplate = null;
                    this.templateFormValues = {};
                    this.showTemplateModal = true;
                },
                selectTemplate(tmpl) {
                    this.selectedTemplate = tmpl;
                    this.templateFormValues = {};
                    for (const f of tmpl.form_fields) {
                        this.templateFormValues[f.name] = f.default !== undefined ? f.default : '';
                    }
                    this.showTemplateModal = true;
                },
                async submitTemplateForm() {
                    if (!this.selectedTemplate) return;
                    this.loading = true;
                    try {
                        const res = await this.apiFetch('/api/v1/connections/from-template', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                template_id: this.selectedTemplate.id,
                                form_values: this.templateFormValues,
                                target_instance_slug: 'horst-suite'
                            })
                        });
                        const data = await res.json();
                        if (res.ok) {
                            alert(`Conexão '${data.name}' criada com sucesso!`);
                            this.showTemplateModal = false;
                            await this.refreshAll();
                        } else {
                            alert('Erro: ' + (data.detail || 'Falha ao criar conexão'));
                        }
                    } catch (e) {
                        alert('Erro de conexão: ' + e);
                    } finally {
                        this.loading = false;
                    }
                },
                addSourceItem() {
                    this.sourcesMapData.sources.push({
                        name: 'Nova Fonte',
                        system: 'novo_sistema',
                        content_types: [],
                        primary_tools: [],
                        guidance: 'Descreva quando o agente deve consultar esta fonte.'
                    });
                },
                removeSourceItem(idx) {
                    this.sourcesMapData.sources.splice(idx, 1);
                },
                async saveSourcesMap() {
                    this.loading = true;
                    try {
                        const res = await this.apiFetch('/api/v1/instances/horst-suite/sources-map', {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(this.sourcesMapData)
                        });
                        if (res && res.ok) {
                            alert('Diretrizes do Mapa de Fontes de Dados atualizadas com sucesso!');
                        }
                    } finally {
                        this.loading = false;
                    }
                },
                async discoverTools(connId) {
                    this.loading = true;
                    try {
                        const res = await this.apiFetch(`/api/v1/connections/${connId}/discover`, { method: 'POST' });
                        const data = await res.json();
                        if (res && res.ok) {
                            alert(`Descoberta concluída! ${data.tools_discovered} ferramentas encontradas.`);
                            await this.fetchTools();
                            await this.fetchConnections();
                        } else {
                            alert('Erro na descoberta: ' + (data.detail || 'Falha ao contatar upstream'));
                        }
                    } catch (e) {
                        alert('Erro de rede: ' + e);
                    } finally {
                        this.loading = false;
                    }
                },
                async reloadInstance(slug) {
                    this.loading = true;
                    try {
                        const res = await this.apiFetch(`/api/v1/instances/${slug}/reload`, { method: 'POST' });
                        if (res && res.ok) {
                            alert(`Instância '${slug}' recarregada com sucesso!`);
                            await this.refreshAll();
                        }
                    } finally {
                        this.loading = false;
                    }
                },
                inspectTool(tool) {
                    this.activeModalTool = tool;
                },
                getEndpointUrl(slug, token) {
                    const loc = window.location;
                    const proto = loc.protocol;
                    const host = loc.host;
                    return `${proto}//${host}/mcp/${slug}/sse?token=${token || 'seu_token'}`;
                },
                copyToClipboard(text) {
                    navigator.clipboard.writeText(text);
                    alert('URL copiada para a área de transferência! Cole diretamente no Paperclip.');
                },
                formatDate(isoString) {
                    if (!isoString) return '-';
                    const d = new Date(isoString);
                    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' (' + d.toLocaleDateString('pt-BR') + ')';
                }
            };
        }
    </script>
</body>
</html>
"""
