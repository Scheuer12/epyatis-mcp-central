"""
Web Dashboard UI para o Epyatis MCP Central.
Interface executiva unificada, aglutinada e centrada em Instâncias e Conexões.
"""

from fastapi.responses import HTMLResponse


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

    <!-- Toast Notifications Container -->
    <div class="fixed top-5 right-5 z-50 flex flex-col gap-2 max-w-sm pointer-events-none">
        <template x-for="t in toasts" :key="t.id">
            <div class="pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg border text-sm font-medium transition-all duration-300 transform translate-y-0"
                 :class="{
                     'bg-emerald-900 border-emerald-700 text-emerald-100': t.type === 'success',
                     'bg-rose-900 border-rose-700 text-rose-100': t.type === 'error',
                     'bg-blue-900 border-blue-700 text-blue-100': t.type === 'info'
                 }">
                <i :class="{
                    'fa-solid fa-circle-check text-emerald-400': t.type === 'success',
                    'fa-solid fa-triangle-exclamation text-rose-400': t.type === 'error',
                    'fa-solid fa-circle-info text-blue-400': t.type === 'info'
                }"></i>
                <span class="flex-1" x-text="t.message"></span>
                <button @click="removeToast(t.id)" class="text-xs opacity-60 hover:opacity-100"><i class="fa-solid fa-xmark"></i></button>
            </div>
        </template>
    </div>

    <!-- Sidebar Lateral Consolidada -->
    <aside class="w-64 bg-slate-900 text-slate-300 flex flex-col flex-shrink-0 border-r border-slate-800">
        <!-- Logo e Título -->
        <div class="p-5 border-b border-slate-800 flex items-center justify-between">
            <div>
                <div class="flex items-center gap-2">
                    <span class="text-xl">⚡</span>
                    <h1 class="text-base font-bold text-white tracking-wide">Epyatis MCP</h1>
                </div>
                <div class="flex items-center gap-2 mt-1">
                    <span class="text-[11px] text-slate-400 font-medium">Central Gateway</span>
                    <span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse mr-1"></span> Ativo
                    </span>
                </div>
            </div>
        </div>

        <!-- Seção do Usuário Ativo & Sessão -->
        <div class="px-4 py-3 bg-slate-950/60 border-b border-slate-800/80 flex items-center justify-between">
            <div class="flex items-center gap-2.5 overflow-hidden">
                <div class="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 text-xs font-bold shrink-0">
                    <i class="fa-solid fa-user"></i>
                </div>
                <div class="overflow-hidden">
                    <div class="text-xs font-semibold text-slate-200 truncate" x-text="currentUser.display_name || currentUser.username || 'Carregando...'"></div>
                    <div class="text-[10px] flex items-center gap-1.5">
                        <template x-if="currentUser.role === 'epy_root'">
                            <span class="text-amber-400 font-semibold flex items-center gap-1"><i class="fa-solid fa-crown text-[9px]"></i> Master Admin</span>
                        </template>
                        <template x-if="currentUser.role !== 'epy_root'">
                            <span class="text-slate-400">Padrão</span>
                        </template>
                    </div>
                </div>
            </div>
            <button @click="showUserModal = true" class="text-slate-400 hover:text-blue-400 text-xs p-1.5 rounded-lg hover:bg-slate-800 transition-colors" title="Trocar Usuário ou Gerenciar Sessão">
                <i class="fa-solid fa-arrow-right-arrow-left"></i>
            </button>
        </div>

        <!-- Navegação Primária Aglutinada (4 Abas Centrais) -->
        <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            <button @click="switchMainTab('instances')" 
                    :class="activeTab === 'instances' ? 'bg-blue-600 text-white shadow-sm' : 'hover:bg-slate-800/70 text-slate-300'"
                    class="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-colors">
                <div class="flex items-center gap-3">
                    <i class="fa-solid fa-cubes-stacked w-4 text-center"></i>
                    <span>Instâncias & Endpoints</span>
                </div>
                <span class="px-1.5 py-0.5 rounded-md text-[10px] font-bold bg-slate-800/60 text-slate-300" x-text="instances.length"></span>
            </button>

            <button @click="switchMainTab('connections')" 
                    :class="activeTab === 'connections' ? 'bg-blue-600 text-white shadow-sm' : 'hover:bg-slate-800/70 text-slate-300'"
                    class="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-colors">
                <div class="flex items-center gap-3">
                    <i class="fa-solid fa-plug w-4 text-center"></i>
                    <span>Cofre de Conexões</span>
                </div>
                <span class="px-1.5 py-0.5 rounded-md text-[10px] font-bold bg-slate-800/60 text-slate-300" x-text="connections.length"></span>
            </button>

            <button @click="switchMainTab('kits')" 
                    :class="activeTab === 'kits' ? 'bg-blue-600 text-white shadow-sm' : 'hover:bg-slate-800/70 text-slate-300'"
                    class="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-colors">
                <div class="flex items-center gap-3">
                    <i class="fa-solid fa-book-bookmark w-4 text-center"></i>
                    <span>Kits de Conhecimento</span>
                </div>
                <span class="px-1.5 py-0.5 rounded-md text-[10px] font-bold bg-slate-800/60 text-slate-300" x-text="dataSourceKits.length"></span>
            </button>

            <button @click="switchMainTab('governance')" 
                    :class="activeTab === 'governance' ? 'bg-blue-600 text-white shadow-sm' : 'hover:bg-slate-800/70 text-slate-300'"
                    class="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-colors">
                <div class="flex items-center gap-3">
                    <i class="fa-solid fa-shield-halved w-4 text-center"></i>
                    <span>Governança & Logs</span>
                </div>
                <span class="w-2 h-2 rounded-full bg-slate-500" :class="overview.total_calls > 0 ? 'bg-emerald-400' : ''"></span>
            </button>
        </nav>

        <!-- Status e Ações Inferiores -->
        <div class="p-4 border-t border-slate-800 bg-slate-950/40 text-[11px] text-slate-400 flex items-center justify-between">
            <div>
                <span class="block text-slate-200 font-semibold" x-text="(toolsTotal || 0) + ' Ferramentas'"></span>
                <span>Porta 8000</span>
            </div>
            <button @click="refreshAll()" :disabled="loading" class="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors" title="Atualizar dados">
                <i class="fa-solid fa-arrows-rotate" :class="loading ? 'animate-spin' : ''"></i>
            </button>
        </div>
    </aside>

    <!-- Painel de Conteúdo Principal -->
    <main class="flex-1 flex flex-col overflow-hidden bg-slate-50">
        <!-- Topbar com Título e Filtro de Visibilidade -->
        <header class="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shadow-xs shrink-0">
            <div>
                <h2 class="text-base font-bold text-slate-800" x-text="pageTitles[activeTab] || 'Epyatis MCP Central'"></h2>
                <p class="text-xs text-slate-500" x-text="pageDescriptions[activeTab] || ''"></p>
            </div>

            <!-- Filtros Globais e Ações Rápidas -->
            <div class="flex items-center gap-3">
                <!-- Filtro de Visibilidade -->
                <div class="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-600">
                    <button @click="visibilityFilter = 'all'; filterContent()" :class="visibilityFilter === 'all' ? 'bg-white text-blue-600 shadow-xs font-semibold' : 'hover:text-slate-900'" class="px-2.5 py-1 rounded-md transition-all">Todos</button>
                    <button @click="visibilityFilter = 'private'; filterContent()" :class="visibilityFilter === 'private' ? 'bg-white text-blue-600 shadow-xs font-semibold' : 'hover:text-slate-900'" class="px-2.5 py-1 rounded-md transition-all">Privados</button>
                    <button @click="visibilityFilter = 'shared'; filterContent()" :class="visibilityFilter === 'shared' ? 'bg-white text-blue-600 shadow-xs font-semibold' : 'hover:text-slate-900'" class="px-2.5 py-1 rounded-md transition-all">Compartilhados</button>
                    <button @click="visibilityFilter = 'public'; filterContent()" :class="visibilityFilter === 'public' ? 'bg-white text-blue-600 shadow-xs font-semibold' : 'hover:text-slate-900'" class="px-2.5 py-1 rounded-md transition-all">Públicos</button>
                </div>

                <!-- Botões de Ação de Acordo com a Aba -->
                <template x-if="activeTab === 'instances'">
                    <button @click="showCreateInstanceModal = true" class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-colors">
                        <i class="fa-solid fa-plus"></i> Nova Instância
                    </button>
                </template>
                <template x-if="activeTab === 'connections'">
                    <button @click="showTemplateModal = true" class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-colors">
                        <i class="fa-solid fa-plus"></i> Conectar Serviço (Receita)
                    </button>
                </template>
                <template x-if="activeTab === 'kits'">
                    <button @click="openCreateKitModal()" class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-colors">
                        <i class="fa-solid fa-plus"></i> Novo Kit de Conhecimento
                    </button>
                </template>
            </div>
        </header>

        <!-- Corpo com Rolagem -->
        <div class="flex-1 overflow-y-auto p-6">

            <!-- ============================================================= -->
            <!-- ABA 1: HUB DE INSTÂNCIAS & STUDIO INTEGRADO                    -->
            <!-- ============================================================= -->
            <div x-show="activeTab === 'instances'" class="space-y-6">

                <!-- Vista de Seleção de Instância / Studio -->
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

                    <!-- Coluna da Esquerda: Lista de Instâncias -->
                    <div class="lg:col-span-4 space-y-3">
                        <div class="flex items-center justify-between pb-2 border-b border-slate-200">
                            <span class="text-xs font-bold uppercase tracking-wider text-slate-500">Instâncias Disponíveis</span>
                            <span class="text-xs text-slate-400" x-text="filteredInstances.length + ' encontradas'"></span>
                        </div>

                        <div class="space-y-2">
                            <template x-for="inst in filteredInstances" :key="inst.id">
                                <div @click="selectInstance(inst.slug)" 
                                     :class="selectedInstanceSlug === inst.slug ? 'ring-2 ring-blue-600 bg-white shadow-md' : 'bg-white hover:bg-slate-50 border border-slate-200/80 shadow-xs'"
                                     class="p-4 rounded-xl cursor-pointer transition-all">
                                    <div class="flex items-start justify-between gap-2">
                                        <div>
                                            <h4 class="text-sm font-bold text-slate-900" x-text="inst.name"></h4>
                                            <span class="text-[11px] font-mono text-slate-400 block mt-0.5" x-text="'slug: ' + inst.slug"></span>
                                        </div>
                                        <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold flex items-center gap-1"
                                              :class="{
                                                  'bg-amber-50 text-amber-700 border border-amber-200': inst.visibility === 'public',
                                                  'bg-blue-50 text-blue-700 border border-blue-200': inst.visibility === 'shared',
                                                  'bg-slate-100 text-slate-600 border border-slate-200': inst.visibility === 'private'
                                              }">
                                            <i class="fa-solid" :class="{ 'fa-globe': inst.visibility === 'public', 'fa-users': inst.visibility === 'shared', 'fa-lock': inst.visibility === 'private' }"></i>
                                            <span x-text="inst.visibility === 'public' ? 'Público' : (inst.visibility === 'shared' ? 'Compartilhado' : 'Privado')"></span>
                                        </span>
                                    </div>
                                    <p class="text-xs text-slate-500 mt-2 line-clamp-2" x-text="inst.description || 'Sem descrição cadastrada.'"></p>
                                    
                                    <div class="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                                        <div class="flex items-center gap-3">
                                            <span class="flex items-center gap-1"><i class="fa-solid fa-plug text-[10px] text-slate-400"></i> <strong class="text-slate-700" x-text="(inst.connections || []).length"></strong></span>
                                            <span class="flex items-center gap-1"><i class="fa-solid fa-wrench text-[10px] text-slate-400"></i> <strong class="text-slate-700" x-text="inst.tools_count || 0"></strong></span>
                                        </div>
                                        <button @click.stop="copyText(getEndpointUrl(inst.slug, (inst.tokens[0] || {}).token), 'URL do Paperclip copiada!')" 
                                                class="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1 hover:underline">
                                            <i class="fa-regular fa-copy"></i> Copiar URL
                                        </button>
                                    </div>
                                </div>
                            </template>

                            <template x-if="filteredInstances.length === 0">
                                <div class="p-6 text-center bg-white rounded-xl border border-dashed border-slate-200 text-slate-400 text-xs">
                                    Nenhuma instância encontrada para este filtro.
                                </div>
                            </template>
                        </div>
                    </div>

                    <!-- Coluna da Direita: Studio / Workstation da Instância Selecionada -->
                    <div class="lg:col-span-8">
                        <template x-if="currentInstanceDetail">
                            <div class="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
                                <!-- Cabeçalho do Studio da Instância -->
                                <div class="p-6 border-b border-slate-200 bg-slate-900 text-white">
                                    <div class="flex flex-wrap items-start justify-between gap-4">
                                        <div>
                                            <div class="flex items-center gap-2">
                                                <h3 class="text-lg font-bold" x-text="currentInstanceDetail.name"></h3>
                                                <!-- Dropdown Rápido de Visibilidade com 1 Clique -->
                                                <div class="relative inline-block" x-data="{ openVis: false }">
                                                    <button @click="openVis = !openVis" 
                                                            class="px-2 py-0.5 rounded-full text-[11px] font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
                                                            :class="{
                                                                'bg-amber-500/20 text-amber-300 border border-amber-500/40': currentInstanceDetail.visibility === 'public',
                                                                'bg-blue-500/20 text-blue-300 border border-blue-500/40': currentInstanceDetail.visibility === 'shared',
                                                                'bg-slate-700 text-slate-300 border border-slate-600': currentInstanceDetail.visibility === 'private'
                                                            }">
                                                        <i class="fa-solid" :class="{ 'fa-globe': currentInstanceDetail.visibility === 'public', 'fa-users': currentInstanceDetail.visibility === 'shared', 'fa-lock': currentInstanceDetail.visibility === 'private' }"></i>
                                                        <span x-text="currentInstanceDetail.visibility === 'public' ? 'Público' : (currentInstanceDetail.visibility === 'shared' ? 'Compartilhado' : 'Privado')"></span>
                                                        <i class="fa-solid fa-chevron-down text-[9px] opacity-70"></i>
                                                    </button>
                                                    <div x-show="openVis" @click.outside="openVis = false" 
                                                         class="absolute left-0 mt-1 w-36 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-20 py-1 text-xs">
                                                        <button @click="setInstanceVisibility(currentInstanceDetail.slug, 'private'); openVis = false" class="w-full text-left px-3 py-1.5 hover:bg-slate-700 text-slate-200 flex items-center gap-2"><i class="fa-solid fa-lock text-slate-400"></i> Privado</button>
                                                        <button @click="setInstanceVisibility(currentInstanceDetail.slug, 'shared'); openVis = false" class="w-full text-left px-3 py-1.5 hover:bg-slate-700 text-blue-300 flex items-center gap-2"><i class="fa-solid fa-users text-blue-400"></i> Compartilhado</button>
                                                        <button @click="setInstanceVisibility(currentInstanceDetail.slug, 'public'); openVis = false" class="w-full text-left px-3 py-1.5 hover:bg-slate-700 text-amber-300 flex items-center gap-2"><i class="fa-solid fa-crown text-amber-400"></i> Público (Root)</button>
                                                    </div>
                                                </div>
                                            </div>
                                            <p class="text-xs text-slate-400 mt-1" x-text="currentInstanceDetail.description || 'Instância operacional MCP agregadora de ferramentas.'"></p>
                                        </div>

                                        <!-- Ações da Instância -->
                                        <div class="flex items-center gap-2">
                                            <button @click="reloadInstance(currentInstanceDetail.slug)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors">
                                                <i class="fa-solid fa-rotate text-slate-400"></i> Recarregar
                                            </button>
                                            <button @click="confirmDeleteInstance(currentInstanceDetail.slug)" class="px-3 py-1.5 bg-rose-950/40 hover:bg-rose-900 border border-rose-800 text-rose-300 rounded-lg text-xs font-medium transition-colors" title="Excluir Instância">
                                                <i class="fa-solid fa-trash-can"></i>
                                            </button>
                                        </div>
                                    </div>

                                    <!-- Banner de Conexão Rápida para o Paperclip -->
                                    <div class="mt-4 p-3 bg-slate-950/80 rounded-lg border border-slate-800 flex items-center justify-between gap-4">
                                        <div class="overflow-hidden">
                                            <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">URL MCP Server-Sent Events (Paperclip / Claude)</span>
                                            <code class="text-xs text-emerald-400 font-mono truncate block mt-0.5" x-text="getEndpointUrl(currentInstanceDetail.slug, (currentInstanceDetail.tokens[0] || {}).token)"></code>
                                        </div>
                                        <button @click="copyText(getEndpointUrl(currentInstanceDetail.slug, (currentInstanceDetail.tokens[0] || {}).token), 'URL do Paperclip copiada!')"
                                                class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shrink-0 transition-colors flex items-center gap-1.5">
                                            <i class="fa-regular fa-copy"></i> Copiar URL
                                        </button>
                                    </div>
                                </div>

                                <!-- Sub-Abas do Studio da Instância -->
                                <div class="border-b border-slate-200 px-6 flex items-center gap-6 text-xs font-semibold bg-slate-50/50">
                                    <button @click="studioTab = 'connections'" :class="studioTab === 'connections' ? 'text-blue-600 border-b-2 border-blue-600 py-3' : 'text-slate-500 hover:text-slate-800 py-3'">
                                        <i class="fa-solid fa-plug mr-1.5"></i> Conexões Vinculadas (<span x-text="(currentInstanceDetail.connections || []).length"></span>)
                                    </button>
                                    <button @click="studioTab = 'sources_map'" :class="studioTab === 'sources_map' ? 'text-blue-600 border-b-2 border-blue-600 py-3' : 'text-slate-500 hover:text-slate-800 py-3'">
                                        <i class="fa-solid fa-book-atlas mr-1.5"></i> Mapa de Conhecimento
                                    </button>
                                    <button @click="studioTab = 'tools'" :class="studioTab === 'tools' ? 'text-blue-600 border-b-2 border-blue-600 py-3' : 'text-slate-500 hover:text-slate-800 py-3'">
                                        <i class="fa-solid fa-wrench mr-1.5"></i> Ferramentas & Toggles (<span x-text="instanceTools.length"></span>)
                                    </button>
                                    <button @click="studioTab = 'tokens'" :class="studioTab === 'tokens' ? 'text-blue-600 border-b-2 border-blue-600 py-3' : 'text-slate-500 hover:text-slate-800 py-3'">
                                        <i class="fa-solid fa-key mr-1.5"></i> Tokens de Acesso (<span x-text="(currentInstanceDetail.tokens || []).length"></span>)
                                    </button>
                                    <button @click="studioTab = 'logs'" :class="studioTab === 'logs' ? 'text-blue-600 border-b-2 border-blue-600 py-3' : 'text-slate-500 hover:text-slate-800 py-3'">
                                        <i class="fa-solid fa-clock-rotate-left mr-1.5"></i> Auditoria Recente
                                    </button>
                                </div>

                                <!-- Conteúdo da Sub-Aba: Conexões Vinculadas -->
                                <div x-show="studioTab === 'connections'" class="p-6 space-y-4">
                                    <div class="flex items-center justify-between">
                                        <div>
                                            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-600">Serviços e Provedores Conectados</h4>
                                            <p class="text-xs text-slate-400">Conexões ativas agregadas nesta instância.</p>
                                        </div>
                                        <!-- Vincular Conexão Existente ou Criar Nova -->
                                        <div class="flex items-center gap-2">
                                            <div class="flex items-center gap-1.5">
                                                <select x-model="attachConnectionId" class="text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white text-slate-700">
                                                    <option value="">Selecione para Vincular...</option>
                                                    <template x-for="c in availableConnectionsToAttach" :key="c.id">
                                                        <option :value="c.id" x-text="c.name + ' (' + c.id + ')'"></option>
                                                    </template>
                                                </select>
                                                <button @click="attachConnection(currentInstanceDetail.slug)" :disabled="!attachConnectionId" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-xs font-semibold disabled:opacity-40 transition-colors">
                                                    Vincular
                                                </button>
                                            </div>
                                            <button @click="openTemplateModalWithTarget(currentInstanceDetail.slug)" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition-colors flex items-center gap-1">
                                                <i class="fa-solid fa-plus text-[10px]"></i> Conectar Novo Serviço
                                            </button>
                                        </div>
                                    </div>

                                    <!-- Lista de Conexões Vinculadas -->
                                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                                        <template x-for="c in currentInstanceDetail.connections" :key="c.id">
                                            <div class="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 flex items-center justify-between">
                                                <div class="flex items-center gap-3 overflow-hidden">
                                                    <div class="w-9 h-9 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs shrink-0">
                                                        <i class="fa-solid" :class="getConnectionIcon(c.id, c.type)"></i>
                                                    </div>
                                                    <div class="overflow-hidden">
                                                        <h5 class="text-xs font-bold text-slate-800 truncate" x-text="c.name"></h5>
                                                        <span class="text-[11px] text-slate-400 font-mono" x-text="'prefix: ' + (c.prefix || c.id) + '__*'"></span>
                                                    </div>
                                                </div>
                                                <button @click="detachConnection(currentInstanceDetail.slug, c.id)" class="text-slate-400 hover:text-rose-600 text-xs p-1 rounded transition-colors" title="Desvincular desta instância">
                                                    <i class="fa-solid fa-link-slash"></i>
                                                </button>
                                            </div>
                                        </template>

                                        <template x-if="(currentInstanceDetail.connections || []).length === 0">
                                            <div class="col-span-2 p-8 text-center border border-dashed border-slate-200 rounded-xl text-slate-400 text-xs">
                                                Nenhuma conexão vinculada a esta instância ainda. Use os botões acima para vincular conexões ativas.
                                            </div>
                                        </template>
                                    </div>
                                </div>

                                <!-- Conteúdo da Sub-Aba: Mapa de Conhecimento (Data Sources Map) -->
                                <div x-show="studioTab === 'sources_map'" class="p-6 space-y-4">
                                    <div class="flex items-center justify-between pb-3 border-b border-slate-200">
                                        <div>
                                            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-700">Instruções Operacionais da IA</h4>
                                            <p class="text-xs text-slate-400">Diretrizes ensinando o agente onde encontrar cada documento e dado nesta instância.</p>
                                        </div>
                                        <div class="flex items-center gap-2">
                                            <!-- Carregar de Kit -->
                                            <select @change="loadKitIntoStudioMap($event.target.value)" class="text-xs border border-slate-300 rounded-lg px-2 py-1.5 bg-white text-slate-700">
                                                <option value="">Carregar de um Kit...</option>
                                                <template x-for="k in dataSourceKits" :key="k.id">
                                                    <option :value="k.id" x-text="k.name"></option>
                                                </template>
                                            </select>
                                            <!-- Salvar como Kit -->
                                            <button @click="openSaveAsKit(currentInstanceDetail.slug)" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium transition-colors">
                                                <i class="fa-solid fa-floppy-disk text-slate-400 mr-1"></i> Salvar como Kit
                                            </button>
                                            <!-- Salvar Alterações -->
                                            <button @click="saveStudioSourcesMap()" :disabled="isSavingMap" class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors flex items-center gap-1.5">
                                                <i class="fa-solid fa-check"></i> <span x-text="isSavingMap ? 'Salvando...' : 'Salvar Alterações'"></span>
                                            </button>
                                        </div>
                                    </div>

                                    <div>
                                        <label class="block text-xs font-medium text-slate-600 mb-1">Nome da Organização / Grupo</label>
                                        <input type="text" x-model="sourcesMapData.organization" class="w-full text-xs border border-slate-300 rounded-lg p-2.5 bg-slate-50/50">
                                    </div>

                                    <!-- Lista de Fontes de Dados -->
                                    <div class="space-y-3 pt-2">
                                        <div class="flex items-center justify-between">
                                            <span class="text-xs font-semibold text-slate-700">Fontes Mapeadas (<span x-text="(sourcesMapData.sources || []).length"></span>)</span>
                                            <button @click="addSourceItem()" class="text-xs text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1">
                                                <i class="fa-solid fa-plus"></i> Adicionar Fonte
                                            </button>
                                        </div>

                                        <template x-for="(s, sIndex) in (sourcesMapData.sources || [])" :key="sIndex">
                                            <div class="p-3.5 rounded-xl border border-slate-200 bg-slate-50/60 space-y-2 relative">
                                                <button @click="removeSourceItem(sIndex)" class="absolute top-3 right-3 text-slate-400 hover:text-rose-600 text-xs p-1" title="Remover Fonte">
                                                    <i class="fa-solid fa-xmark"></i>
                                                </button>
                                                <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pr-6">
                                                    <div>
                                                        <label class="block text-[10px] font-semibold text-slate-500 uppercase">Nome da Fonte</label>
                                                        <input type="text" x-model="s.name" class="w-full text-xs border border-slate-300 rounded-md p-1.5 bg-white">
                                                    </div>
                                                    <div>
                                                        <label class="block text-[10px] font-semibold text-slate-500 uppercase">Identificador de Sistema</label>
                                                        <input type="text" x-model="s.system" class="w-full text-xs border border-slate-300 rounded-md p-1.5 bg-white">
                                                    </div>
                                                </div>
                                                <div>
                                                    <label class="block text-[10px] font-semibold text-slate-500 uppercase">Diretriz de Consulta (Guidance para a IA)</label>
                                                    <textarea x-model="s.guidance" rows="2" class="w-full text-xs border border-slate-300 rounded-md p-1.5 bg-white"></textarea>
                                                </div>
                                            </div>
                                        </template>
                                    </div>
                                </div>

                                <!-- Conteúdo da Sub-Aba: Ferramentas & Toggles -->
                                <div x-show="studioTab === 'tools'" class="p-6 space-y-4">
                                    <div class="flex items-center justify-between">
                                        <div>
                                            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-600">Ferramentas Agregadas nesta Instância</h4>
                                            <p class="text-xs text-slate-400">Ative ou desative ferramentas instantaneamente para o agente.</p>
                                        </div>
                                        <input type="text" x-model="instanceToolFilter" placeholder="Buscar ferramenta..." class="text-xs border border-slate-300 rounded-lg px-3 py-1.5 w-64">
                                    </div>

                                    <div class="space-y-2 max-h-96 overflow-y-auto pr-1">
                                        <template x-for="t in filteredInstanceTools" :key="t.id">
                                            <div class="p-3 rounded-xl border border-slate-200 bg-white flex items-center justify-between hover:border-slate-300 transition-colors">
                                                <div class="overflow-hidden pr-4">
                                                    <div class="flex items-center gap-2">
                                                        <code class="text-xs font-mono font-semibold text-blue-700" x-text="t.name"></code>
                                                        <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 font-mono" x-text="t.connection_id"></span>
                                                    </div>
                                                    <p class="text-xs text-slate-500 mt-1 line-clamp-1" x-text="t.description || 'Sem descrição.'"></p>
                                                </div>
                                                <!-- Toggle Switch -->
                                                <button @click="toggleInstanceTool(currentInstanceDetail.slug, t.name)" 
                                                        class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-hidden"
                                                        :class="t.is_enabled ? 'bg-blue-600' : 'bg-slate-200'">
                                                    <span class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out"
                                                          :class="t.is_enabled ? 'translate-x-4' : 'translate-x-0'"></span>
                                                </button>
                                            </div>
                                        </template>

                                        <template x-if="filteredInstanceTools.length === 0">
                                            <div class="p-8 text-center text-slate-400 text-xs">
                                                Nenhuma ferramenta encontrada para o filtro atual.
                                            </div>
                                        </template>
                                    </div>
                                </div>

                                <!-- Conteúdo da Sub-Aba: Tokens -->
                                <div x-show="studioTab === 'tokens'" class="p-6 space-y-4">
                                    <div class="flex items-center justify-between">
                                        <div>
                                            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-600">Tokens de Acesso da Instância</h4>
                                            <p class="text-xs text-slate-400">Tokens usados pelo Paperclip ou outros clientes para autenticar nesta instância.</p>
                                        </div>
                                        <button @click="addTokenToCurrentInstance()" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition-colors flex items-center gap-1">
                                            <i class="fa-solid fa-plus text-[10px]"></i> Novo Token
                                        </button>
                                    </div>

                                    <div class="space-y-2">
                                        <template x-for="t in currentInstanceDetail.tokens" :key="t.id">
                                            <div class="p-3 rounded-xl border border-slate-200 bg-slate-50/50 flex items-center justify-between">
                                                <div>
                                                    <span class="text-xs font-semibold text-slate-700 block" x-text="t.label || 'Token'"></span>
                                                    <code class="text-xs font-mono text-slate-500" x-text="t.token"></code>
                                                </div>
                                                <button @click="copyText(t.token, 'Token copiado!')" class="text-xs text-blue-600 hover:text-blue-800 font-medium px-2 py-1">
                                                    Copiar Token
                                                </button>
                                            </div>
                                        </template>
                                    </div>
                                </div>

                                <!-- Conteúdo da Sub-Aba: Logs -->
                                <div x-show="studioTab === 'logs'" class="p-6 space-y-3">
                                    <div class="flex items-center justify-between pb-2 border-b border-slate-200">
                                        <span class="text-xs font-bold uppercase tracking-wider text-slate-600">Últimas Execuções da Instância</span>
                                        <button @click="fetchInstanceLogs(currentInstanceDetail.slug)" class="text-xs text-blue-600 hover:underline">Atualizar Logs</button>
                                    </div>
                                    <div class="space-y-1.5 max-h-80 overflow-y-auto">
                                        <template x-for="log in instanceLogs" :key="log.id">
                                            <div class="p-2.5 rounded-lg border border-slate-100 bg-slate-50 text-xs flex items-center justify-between">
                                                <div class="flex items-center gap-2">
                                                    <span class="w-2 h-2 rounded-full" :class="log.status === 'success' ? 'bg-emerald-500' : 'bg-rose-500'"></span>
                                                    <code class="font-mono font-bold text-slate-800" x-text="log.tool_name"></code>
                                                </div>
                                                <div class="flex items-center gap-3 text-slate-400 font-mono text-[11px]">
                                                    <span x-text="log.execution_time_ms + 'ms'"></span>
                                                    <span x-text="formatDate(log.timestamp)"></span>
                                                </div>
                                            </div>
                                        </template>
                                        <template x-if="instanceLogs.length === 0">
                                            <div class="p-6 text-center text-slate-400 text-xs">Nenhum log registrado para esta instância recentemente.</div>
                                        </template>
                                    </div>
                                </div>
                            </div>
                        </template>

                        <template x-if="!currentInstanceDetail">
                            <div class="bg-white rounded-xl border border-dashed border-slate-200 p-12 text-center text-slate-400">
                                <i class="fa-solid fa-hand-pointer text-3xl mb-3 text-slate-300"></i>
                                <h4 class="text-sm font-semibold text-slate-600">Selecione uma Instância</h4>
                                <p class="text-xs mt-1">Clique em uma instância na coluna ao lado para abrir o Studio e gerenciar suas conexões, diretrizes e ferramentas.</p>
                            </div>
                        </template>
                    </div>

                </div>
            </div>

            <!-- ============================================================= -->
            <!-- ABA 2: COFRE DE CONEXÕES & RECEITAS (TEMPLATES)               -->
            <!-- ============================================================= -->
            <div x-show="activeTab === 'connections'" class="space-y-6">
                <!-- Sub-Navegação interna da Aba Conexões -->
                <div class="flex items-center justify-between border-b border-slate-200 pb-3">
                    <div class="flex items-center gap-4 text-xs font-semibold">
                        <button @click="vaultSubTab = 'active'" :class="vaultSubTab === 'active' ? 'text-blue-600 border-b-2 border-blue-600 pb-3' : 'text-slate-500 hover:text-slate-800 pb-3'">
                            <i class="fa-solid fa-link mr-1"></i> Conexões Ativas (<span x-text="connections.length"></span>)
                        </button>
                        <button @click="vaultSubTab = 'templates'" :class="vaultSubTab === 'templates' ? 'text-blue-600 border-b-2 border-blue-600 pb-3' : 'text-slate-500 hover:text-slate-800 pb-3'">
                            <i class="fa-solid fa-wand-magic-sparkles mr-1"></i> Receitas de Conexão (Templates)
                        </button>
                    </div>
                </div>

                <!-- Sub-Aba: Conexões Ativas -->
                <div x-show="vaultSubTab === 'active'" class="space-y-4">
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <template x-for="c in filteredConnections" :key="c.id">
                            <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
                                <div>
                                    <div class="flex items-start justify-between gap-2">
                                        <div class="flex items-center gap-3">
                                            <div class="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center text-sm font-bold shrink-0 border border-blue-100">
                                                <i class="fa-solid" :class="getConnectionIcon(c.id, c.type)"></i>
                                            </div>
                                            <div>
                                                <h4 class="text-sm font-bold text-slate-800" x-text="c.name"></h4>
                                                <span class="text-[11px] font-mono text-slate-400" x-text="'id: ' + c.id"></span>
                                            </div>
                                        </div>
                                        <!-- Visibility Pill com Dropdown Rápido -->
                                        <div class="relative inline-block" x-data="{ openVisConn: false }">
                                            <button @click="openVisConn = !openVisConn" 
                                                    class="px-2 py-0.5 rounded-full text-[10px] font-semibold flex items-center gap-1 cursor-pointer"
                                                    :class="{
                                                        'bg-amber-50 text-amber-700 border border-amber-200': c.visibility === 'public',
                                                        'bg-blue-50 text-blue-700 border border-blue-200': c.visibility === 'shared',
                                                        'bg-slate-100 text-slate-600 border border-slate-200': c.visibility === 'private'
                                                    }">
                                                <i class="fa-solid" :class="{ 'fa-globe': c.visibility === 'public', 'fa-users': c.visibility === 'shared', 'fa-lock': c.visibility === 'private' }"></i>
                                                <span x-text="c.visibility === 'public' ? 'Público' : (c.visibility === 'shared' ? 'Compartilhado' : 'Privado')"></span>
                                                <i class="fa-solid fa-chevron-down text-[8px] opacity-60"></i>
                                            </button>
                                            <div x-show="openVisConn" @click.outside="openVisConn = false" class="absolute right-0 mt-1 w-32 bg-white border border-slate-200 rounded-lg shadow-lg z-20 py-1 text-xs">
                                                <button @click="setConnectionVisibility(c.id, 'private'); openVisConn = false" class="w-full text-left px-3 py-1 hover:bg-slate-50 text-slate-700 flex items-center gap-1.5"><i class="fa-solid fa-lock text-slate-400 text-[10px]"></i> Privado</button>
                                                <button @click="setConnectionVisibility(c.id, 'shared'); openVisConn = false" class="w-full text-left px-3 py-1 hover:bg-slate-50 text-blue-700 flex items-center gap-1.5"><i class="fa-solid fa-users text-blue-500 text-[10px]"></i> Compartilhado</button>
                                                <button @click="setConnectionVisibility(c.id, 'public'); openVisConn = false" class="w-full text-left px-3 py-1 hover:bg-slate-50 text-amber-700 flex items-center gap-1.5"><i class="fa-solid fa-crown text-amber-500 text-[10px]"></i> Público (Root)</button>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                                        <span class="font-mono text-[11px]" x-text="'prefix: ' + (c.prefix || c.id) + '__*'"></span>
                                        <span class="px-2 py-0.5 rounded bg-slate-100 text-[10px] font-semibold uppercase text-slate-600" x-text="c.type"></span>
                                    </div>
                                </div>

                                <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                                    <div class="flex items-center gap-2">
                                        <button @click="discoverTools(c.id)" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md font-medium text-[11px] transition-colors" title="Redescobrir ferramentas">
                                            <i class="fa-solid fa-arrows-rotate mr-1 text-slate-500"></i> Redescobrir
                                        </button>
                                        <button @click="openSaveAsTemplate(c)" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md font-medium text-[11px] transition-colors" title="Salvar configuração como modelo">
                                            <i class="fa-solid fa-bookmark mr-1 text-slate-500"></i> Modelo
                                        </button>
                                    </div>
                                    <button @click="confirmDeleteConnection(c.id)" class="text-slate-400 hover:text-rose-600 p-1 transition-colors" title="Excluir Conexão">
                                        <i class="fa-solid fa-trash-can text-xs"></i>
                                    </button>
                                </div>
                            </div>
                        </template>
                    </div>
                </div>

                <!-- Sub-Aba: Receitas de Conexão (Templates) -->
                <div x-show="vaultSubTab === 'templates'" class="space-y-4">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold uppercase tracking-wider text-slate-500">Catálogo de Receitas Pré-Configuradas</span>
                        <span class="text-xs text-slate-400">Clique para conectar em 1 clique</span>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <template x-for="t in templates" :key="t.id">
                            <div class="bg-white p-5 rounded-xl border border-slate-200 hover:border-blue-400 hover:shadow-md transition-all flex flex-col justify-between">
                                <div>
                                    <div class="flex items-center gap-3">
                                        <div class="w-10 h-10 rounded-xl bg-blue-600/10 text-blue-600 flex items-center justify-center text-sm font-bold shrink-0">
                                            <i class="fa-solid" :class="t.icon || 'fa-plug'"></i>
                                        </div>
                                        <div>
                                            <h4 class="text-sm font-bold text-slate-800" x-text="t.name"></h4>
                                            <span class="text-[10px] font-semibold text-blue-600 uppercase" x-text="t.category || 'Conector'"></span>
                                        </div>
                                    </div>
                                    <p class="text-xs text-slate-500 mt-3" x-text="t.description"></p>
                                </div>
                                <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                                    <span class="text-[11px] text-slate-400" x-text="(t.form_fields || []).length + ' campos'"></span>
                                    <button @click="selectTemplate(t)" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5">
                                        <i class="fa-solid fa-wand-magic-sparkles text-[10px]"></i> Conectar
                                    </button>
                                </div>
                            </div>
                        </template>
                    </div>
                </div>
            </div>

            <!-- ============================================================= -->
            <!-- ABA 3: KITS DE CONHECIMENTO OPERACIONAL                       -->
            <!-- ============================================================= -->
            <div x-show="activeTab === 'kits'" class="space-y-4">
                <div class="flex items-center justify-between pb-2 border-b border-slate-200">
                    <div>
                        <h3 class="text-xs font-bold uppercase tracking-wider text-slate-700">Kits de Conhecimento Reutilizáveis</h3>
                        <p class="text-xs text-slate-400">Pacotes prontos de instruções e diretrizes para aplicar em qualquer instância.</p>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <template x-for="k in filteredKits" :key="k.id">
                        <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
                            <div>
                                <div class="flex items-start justify-between gap-2">
                                    <div>
                                        <h4 class="text-sm font-bold text-slate-800" x-text="k.name"></h4>
                                        <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 font-semibold text-slate-600 uppercase" x-text="k.category || 'Geral'"></span>
                                    </div>
                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold"
                                          :class="k.visibility === 'public' ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-blue-50 text-blue-700 border border-blue-200'">
                                        <span x-text="k.visibility === 'public' ? 'Público' : 'Compartilhado'"></span>
                                    </span>
                                </div>
                                <p class="text-xs text-slate-500 mt-2" x-text="k.description || 'Sem descrição.'"></p>
                                <div class="mt-3 text-xs text-slate-400 font-medium">
                                    <i class="fa-solid fa-list-check mr-1"></i> <span x-text="(k.sources || []).length + ' fontes cadastradas'"></span>
                                </div>
                            </div>

                            <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                                <button @click="applyKitToPrompt(k.id)" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition-colors flex items-center gap-1">
                                    <i class="fa-solid fa-arrow-right-to-bracket text-[10px]"></i> Aplicar em Instância
                                </button>
                                <button @click="deleteKit(k.id)" class="text-slate-400 hover:text-rose-600 p-1 text-xs">
                                    <i class="fa-solid fa-trash-can"></i>
                                </button>
                            </div>
                        </div>
                    </template>
                </div>
            </div>

            <!-- ============================================================= -->
            <!-- ABA 4: GOVERNANÇA, USUÁRIOS & TELEMETRIA                      -->
            <!-- ============================================================= -->
            <div x-show="activeTab === 'governance'" class="space-y-6">
                <div class="flex items-center gap-4 text-xs font-semibold border-b border-slate-200 pb-3">
                    <button @click="govSubTab = 'users'" :class="govSubTab === 'users' ? 'text-blue-600 border-b-2 border-blue-600 pb-3' : 'text-slate-500 hover:text-slate-800 pb-3'">
                        <i class="fa-solid fa-users mr-1"></i> Usuários & Sessões (<span x-text="usersList.length"></span>)
                    </button>
                    <button @click="govSubTab = 'logs'" :class="govSubTab === 'logs' ? 'text-blue-600 border-b-2 border-blue-600 pb-3' : 'text-slate-500 hover:text-slate-800 pb-3'">
                        <i class="fa-solid fa-list-ul mr-1"></i> Logs de Auditoria Globais
                    </button>
                    <button @click="govSubTab = 'overview'" :class="govSubTab === 'overview' ? 'text-blue-600 border-b-2 border-blue-600 pb-3' : 'text-slate-500 hover:text-slate-800 pb-3'">
                        <i class="fa-solid fa-chart-pie mr-1"></i> Métricas do Sistema
                    </button>
                </div>

                <!-- Sub-Aba: Usuários -->
                <div x-show="govSubTab === 'users'" class="space-y-4">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold uppercase tracking-wider text-slate-500">Usuários Cadastrados</span>
                        <button @click="showCreateUserModal = true" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1">
                            <i class="fa-solid fa-user-plus text-[10px]"></i> Novo Usuário
                        </button>
                    </div>

                    <div class="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
                        <table class="w-full text-left text-xs text-slate-600">
                            <thead class="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase text-[10px]">
                                <tr>
                                    <th class="p-3.5">Nome / Usuário</th>
                                    <th class="p-3.5">Função</th>
                                    <th class="p-3.5">Criado Em</th>
                                    <th class="p-3.5 text-right">Ação</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-100">
                                <template x-for="u in usersList" :key="u.id">
                                    <tr class="hover:bg-slate-50">
                                        <td class="p-3.5">
                                            <span class="font-bold text-slate-800" x-text="u.display_name || u.username"></span>
                                            <span class="text-[11px] text-slate-400 block font-mono" x-text="'@' + u.username"></span>
                                        </td>
                                        <td class="p-3.5">
                                            <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold"
                                                  :class="u.role === 'epy_root' ? 'bg-amber-100 text-amber-800 border border-amber-300' : 'bg-slate-100 text-slate-600'">
                                                <span x-text="u.role === 'epy_root' ? 'Master Admin' : 'Padrão'"></span>
                                            </span>
                                        </td>
                                        <td class="p-3.5 text-slate-400" x-text="formatDate(u.created_at)"></td>
                                        <td class="p-3.5 text-right">
                                            <button @click="switchUserAccount(u.username)" class="text-xs text-blue-600 hover:text-blue-800 font-semibold">
                                                Alternar para este Usuário
                                            </button>
                                        </td>
                                    </tr>
                                </template>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Sub-Aba: Logs Globais -->
                <div x-show="govSubTab === 'logs'" class="space-y-3">
                    <div class="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
                        <table class="w-full text-left text-xs text-slate-600">
                            <thead class="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase text-[10px]">
                                <tr>
                                    <th class="p-3.5">Status</th>
                                    <th class="p-3.5">Instância</th>
                                    <th class="p-3.5">Ferramenta</th>
                                    <th class="p-3.5">Latência</th>
                                    <th class="p-3.5">Timestamp</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-100">
                                <template x-for="l in recentLogs" :key="l.id">
                                    <tr class="hover:bg-slate-50">
                                        <td class="p-3.5">
                                            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold"
                                                  :class="l.status === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'"
                                                  x-text="l.status"></span>
                                        </td>
                                        <td class="p-3.5 font-mono text-slate-700" x-text="l.instance_slug || '-'"></td>
                                        <td class="p-3.5 font-mono font-semibold text-blue-700" x-text="l.tool_name"></td>
                                        <td class="p-3.5 font-mono text-slate-500" x-text="l.execution_time_ms + ' ms'"></td>
                                        <td class="p-3.5 text-slate-400 font-mono text-[11px]" x-text="formatDate(l.timestamp)"></td>
                                    </tr>
                                </template>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Sub-Aba: Métricas Overview -->
                <div x-show="govSubTab === 'overview'" class="space-y-4">
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                            <span class="text-xs text-slate-400 font-medium">Instâncias Ativas</span>
                            <div class="text-2xl font-bold text-slate-900 mt-1" x-text="overview.active_instances || 0"></div>
                        </div>
                        <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                            <span class="text-xs text-slate-400 font-medium">Conexões Upstream</span>
                            <div class="text-2xl font-bold text-slate-900 mt-1" x-text="overview.total_connections || 0"></div>
                        </div>
                        <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                            <span class="text-xs text-slate-400 font-medium">Total de Ferramentas</span>
                            <div class="text-2xl font-bold text-slate-900 mt-1" x-text="overview.total_tools || 0"></div>
                        </div>
                        <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                            <span class="text-xs text-slate-400 font-medium">Taxa de Sucesso</span>
                            <div class="text-2xl font-bold text-emerald-600 mt-1" x-text="(overview.success_rate || 100) + '%'"></div>
                        </div>
                    </div>
                </div>
            </div>

        </div>
    </main>

    <!-- ================================================================= -->
    <!-- MODAIS DO SISTEMA                                                 -->
    <!-- ================================================================= -->

    <!-- Modal 1: Criar Nova Instância -->
    <div x-show="showCreateInstanceModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4" @click.self="showCreateInstanceModal = false">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-slate-100">
                <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-cubes-stacked text-blue-600"></i> Criar Nova Instância MCP
                </h3>
                <button @click="showCreateInstanceModal = false" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-medium text-slate-600 mb-1">Nome da Instância</label>
                    <input type="text" x-model="newInstanceForm.name" placeholder="Ex: Finance Operational Suite" class="w-full text-xs border border-slate-300 rounded-lg p-2.5">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-600 mb-1">Identificador de URL (Slug)</label>
                    <input type="text" x-model="newInstanceForm.slug" placeholder="Ex: finance-suite" class="w-full text-xs border border-slate-300 rounded-lg p-2.5 font-mono">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-600 mb-1">Descrição</label>
                    <textarea x-model="newInstanceForm.description" rows="2" placeholder="Finalidade deste endpoint para os agentes..." class="w-full text-xs border border-slate-300 rounded-lg p-2.5"></textarea>
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-600 mb-1">Visibilidade</label>
                    <select x-model="newInstanceForm.visibility" class="w-full text-xs border border-slate-300 rounded-lg p-2.5 bg-white">
                        <option value="private">Privado (Somente Você)</option>
                        <option value="shared">Compartilhado (Equipe)</option>
                        <option value="public" :disabled="currentUser.role !== 'epy_root'">Público (Requer Master Admin)</option>
                    </select>
                </div>
            </div>
            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button @click="showCreateInstanceModal = false" class="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-lg">Cancelar</button>
                <button @click="createInstanceSubmit()" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs">Criar Instância</button>
            </div>
        </div>
    </div>

    <!-- Modal 2: Wizard de Template / Nova Conexão -->
    <div x-show="showTemplateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4" @click.self="showTemplateModal = false">
        <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
            <div class="flex items-center justify-between pb-2 border-b border-slate-100">
                <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-wand-magic-sparkles text-blue-600"></i>
                    <span x-text="selectedTemplate ? 'Conectar: ' + selectedTemplate.name : 'Conectar Novo Serviço'"></span>
                </h3>
                <button @click="showTemplateModal = false" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark"></i></button>
            </div>

            <!-- Se nenhum template selecionado, mostra lista rápida -->
            <template x-if="!selectedTemplate">
                <div class="space-y-2">
                    <p class="text-xs text-slate-500">Escolha uma receita para iniciar o assistente guiado:</p>
                    <div class="grid grid-cols-1 gap-2">
                        <template x-for="t in templates" :key="t.id">
                            <div @click="selectTemplate(t)" class="p-3 rounded-xl border border-slate-200 hover:border-blue-500 hover:bg-blue-50/30 cursor-pointer flex items-center justify-between transition-all">
                                <div class="flex items-center gap-3">
                                    <i class="fa-solid text-blue-600" :class="t.icon || 'fa-plug'"></i>
                                    <div>
                                        <div class="text-xs font-bold text-slate-800" x-text="t.name"></div>
                                        <div class="text-[11px] text-slate-500" x-text="t.description"></div>
                                    </div>
                                </div>
                                <i class="fa-solid fa-chevron-right text-xs text-slate-300"></i>
                            </div>
                        </template>
                    </div>
                </div>
            </template>

            <!-- Formulário Dinâmico do Template Selecionado -->
            <template x-if="selectedTemplate">
                <div class="space-y-3">
                    <p class="text-xs text-slate-500" x-text="selectedTemplate.description"></p>
                    <template x-for="field in (selectedTemplate.form_fields || [])" :key="field.id">
                        <div>
                            <label class="block text-xs font-medium text-slate-600 mb-1" x-text="field.label + (field.required ? ' *' : '')"></label>
                            <input :type="field.type === 'password' ? 'password' : 'text'" 
                                   x-model="templateFormValues[field.id]" 
                                   :placeholder="field.description || ''" 
                                   class="w-full text-xs border border-slate-300 rounded-lg p-2.5">
                        </div>
                    </template>
                    <div class="pt-2">
                        <label class="block text-xs font-medium text-slate-600 mb-1">Vincular diretamente à Instância</label>
                        <select x-model="templateTargetInstanceSlug" class="w-full text-xs border border-slate-300 rounded-lg p-2.5 bg-white">
                            <option value="">Não vincular agora (deixar no cofre)</option>
                            <template x-for="inst in instances" :key="inst.slug">
                                <option :value="inst.slug" x-text="inst.name + ' (' + inst.slug + ')'"></option>
                            </template>
                        </select>
                    </div>
                </div>
            </template>

            <div class="flex items-center justify-between pt-3 border-t border-slate-100">
                <button @click="selectedTemplate ? (selectedTemplate = null) : (showTemplateModal = false)" class="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-lg">
                    <span x-text="selectedTemplate ? 'Voltar' : 'Cancelar'"></span>
                </button>
                <template x-if="selectedTemplate">
                    <button @click="submitTemplateForm()" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs">Concluir Conexão</button>
                </template>
            </div>
        </div>
    </div>

    <!-- Modal 3: Troca Rápida de Usuário & Sessão -->
    <div x-show="showUserModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4" @click.self="showUserModal = false">
        <div class="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-slate-100">
                <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-users text-blue-600"></i> Alternar Usuário Ativo
                </h3>
                <button @click="showUserModal = false" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-2">
                <template x-for="u in usersList" :key="u.id">
                    <div @click="switchUserAccount(u.username); showUserModal = false" 
                         :class="currentUser.username === u.username ? 'bg-blue-50 border-blue-300' : 'hover:bg-slate-50 border-slate-200'"
                         class="p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all">
                        <div>
                            <span class="text-xs font-bold text-slate-800" x-text="u.display_name || u.username"></span>
                            <span class="text-[11px] text-slate-400 block font-mono" x-text="'@' + u.username"></span>
                        </div>
                        <template x-if="u.role === 'epy_root'">
                            <span class="text-amber-500 text-xs font-bold" title="Master Admin"><i class="fa-solid fa-crown"></i></span>
                        </template>
                    </div>
                </template>
            </div>
        </div>
    </div>

    <!-- Modal 4: Criar Novo Usuário -->
    <div x-show="showCreateUserModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4" @click.self="showCreateUserModal = false">
        <div class="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-slate-100">
                <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-user-plus text-blue-600"></i> Criar Novo Usuário
                </h3>
                <button @click="showCreateUserModal = false" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-medium text-slate-600 mb-1">Nome de Exibição</label>
                    <input type="text" x-model="newUserForm.display_name" placeholder="Ex: Analista de Operações" class="w-full text-xs border border-slate-300 rounded-lg p-2.5">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-600 mb-1">Username (Login)</label>
                    <input type="text" x-model="newUserForm.username" placeholder="Ex: analista_ops" class="w-full text-xs border border-slate-300 rounded-lg p-2.5 font-mono">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-600 mb-1">Função / Perfil</label>
                    <select x-model="newUserForm.role" class="w-full text-xs border border-slate-300 rounded-lg p-2.5 bg-white">
                        <option value="standard">Padrão</option>
                        <option value="epy_root">Master Admin</option>
                    </select>
                </div>
            </div>
            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button @click="showCreateUserModal = false" class="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-lg">Cancelar</button>
                <button @click="createUserSubmit()" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs">Salvar</button>
            </div>
        </div>
    </div>

    <!-- Modal 5: Salvar como Template -->
    <div x-show="showSaveAsTemplateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4" @click.self="showSaveAsTemplateModal = false">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-slate-100">
                <h3 class="text-sm font-bold text-slate-800">Salvar Conexão como Modelo Reutilizável</h3>
                <button @click="showSaveAsTemplateModal = false" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-medium text-slate-600 mb-1">Nome do Modelo</label>
                    <input type="text" x-model="newTemplateName" class="w-full text-xs border border-slate-300 rounded-lg p-2.5">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-600 mb-1">Descrição</label>
                    <textarea x-model="newTemplateDesc" rows="2" class="w-full text-xs border border-slate-300 rounded-lg p-2.5"></textarea>
                </div>
            </div>
            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button @click="showSaveAsTemplateModal = false" class="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-lg">Cancelar</button>
                <button @click="saveConnectionAsTemplateSubmit()" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs">Salvar Modelo</button>
            </div>
        </div>
    </div>

    <!-- Modal 6: Salvar como Kit -->
    <div x-show="showSaveAsKitModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4" @click.self="showSaveAsKitModal = false">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-slate-100">
                <h3 class="text-sm font-bold text-slate-800">Salvar Mapa como Kit de Conhecimento</h3>
                <button @click="showSaveAsKitModal = false" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-medium text-slate-600 mb-1">Nome do Kit</label>
                    <input type="text" x-model="newKitName" placeholder="Ex: Kit Operacional Padrão" class="w-full text-xs border border-slate-300 rounded-lg p-2.5">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-600 mb-1">Categoria</label>
                    <input type="text" x-model="newKitCategory" placeholder="Ex: Operações, Finanças" class="w-full text-xs border border-slate-300 rounded-lg p-2.5">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-600 mb-1">Descrição</label>
                    <textarea x-model="newKitDesc" rows="2" class="w-full text-xs border border-slate-300 rounded-lg p-2.5"></textarea>
                </div>
            </div>
            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button @click="showSaveAsKitModal = false" class="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-lg">Cancelar</button>
                <button @click="saveKitSubmit()" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs">Salvar Kit</button>
            </div>
        </div>
    </div>

    <!-- Modal 7: Confirmação Segura de Exclusão -->
    <div x-show="showConfirmModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4" @click.self="showConfirmModal = false">
        <div class="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div class="flex items-center gap-3 text-rose-600">
                <div class="w-10 h-10 rounded-full bg-rose-100 flex items-center justify-center text-rose-600 text-lg shrink-0">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                </div>
                <div>
                    <h3 class="text-sm font-bold text-slate-800" x-text="confirmTitle"></h3>
                    <p class="text-xs text-slate-500 mt-0.5" x-text="confirmMessage"></p>
                </div>
            </div>
            <div class="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button @click="showConfirmModal = false" class="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-lg">Cancelar</button>
                <button @click="executeConfirmedAction()" class="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold shadow-xs">Confirmar Exclusão</button>
            </div>
        </div>
    </div>

    <!-- Modal 8: Autenticação Administrativa Inicial -->
    <div x-show="showAuthModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-xs p-4">
        <div class="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200 text-center space-y-4">
            <div class="w-12 h-12 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mx-auto text-xl">
                <i class="fa-solid fa-shield-halved"></i>
            </div>
            <div>
                <h3 class="text-base font-bold text-slate-800">Autenticação Administrativa</h3>
                <p class="text-xs text-slate-500 mt-1">Informe sua chave mestra administrativa para conectar ao Central.</p>
            </div>
            <div>
                <input type="password" x-model="authKeyInput" placeholder="Chave de Admin..." class="w-full text-xs border border-slate-300 rounded-lg p-2.5 text-center font-mono">
            </div>
            <button @click="saveAdminKey()" class="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors">
                Acessar Central
            </button>
        </div>
    </div>

    <!-- Script Alpine.js do Aplicativo -->
    <script>
        function centralApp() {
            return {
                activeTab: 'instances',
                studioTab: 'connections',
                vaultSubTab: 'active',
                govSubTab: 'users',
                visibilityFilter: 'all',
                loading: false,
                adminKey: localStorage.getItem('central_admin_key') || '',
                sessionToken: localStorage.getItem('central_session_token') || '',
                showAuthModal: false,
                showUserModal: false,
                showCreateUserModal: false,
                showCreateInstanceModal: false,
                showTemplateModal: false,
                showSaveAsTemplateModal: false,
                showSaveAsKitModal: false,
                showConfirmModal: false,
                showInstantiateModal: false,
                authKeyInput: '',
                currentUser: { username: '', role: 'standard', display_name: '', is_master_admin: false },
                usersList: [],
                overview: {},
                connections: [],
                instances: [],
                dataSourceKits: [],
                templates: [],
                recentLogs: [],
                toolsTotal: 0,
                selectedInstanceSlug: null,
                currentInstanceDetail: null,
                instanceTools: [],
                instanceToolFilter: '',
                instanceLogs: [],
                attachConnectionId: '',
                templateTargetInstanceSlug: '',
                selectedTemplate: null,
                templateFormValues: {},
                sourcesMapData: { organization: 'Epyatis', sources: [] },
                isSavingMap: false,
                toasts: [],
                newInstanceForm: { name: '', slug: '', description: '', visibility: 'shared' },
                newUserForm: { username: '', display_name: '', role: 'standard' },
                saveTemplateTargetConn: null,
                newTemplateName: '',
                newTemplateDesc: '',
                saveKitTargetInstance: null,
                newKitName: '',
                newKitCategory: 'Operações',
                newKitDesc: '',
                confirmTitle: '',
                confirmMessage: '',
                pendingConfirmAction: null,
                pageTitles: {
                    instances: 'Instâncias & Endpoints MCP',
                    connections: 'Cofre de Conexões Upstream',
                    kits: 'Kits de Conhecimento Operacional',
                    governance: 'Governança & Telemetria',
                    dashboard: 'Instâncias & Endpoints MCP'
                },
                pageDescriptions: {
                    instances: 'Gerencie os pontos de acesso exclusivos dos seus Agentes de IA, suas conexões vinculadas e diretrizes de dados.',
                    connections: 'Conectores autenticados e biblioteca de receitas prontas para integração de novos serviços.',
                    kits: 'Pacotes reutilizáveis de mapeamento de dados para guiar agentes em diferentes instâncias.',
                    governance: 'Controle de usuários, sessões ativas, métricas de execução e logs detalhados de auditoria.'
                },

                showToast(message, type = 'success') {
                    const id = Date.now() + Math.random();
                    this.toasts.push({ id, message, type });
                    setTimeout(() => this.removeToast(id), 3500);
                },
                removeToast(id) {
                    this.toasts = this.toasts.filter(t => t.id !== id);
                },

                copyText(text, label) {
                    if (!text) return;
                    navigator.clipboard.writeText(text);
                    this.showToast(label || 'Copiado para a área de transferência!', 'success');
                },

                switchMainTab(tab) {
                    this.activeTab = tab;
                    if (tab === 'instances' && !this.selectedInstanceSlug && this.instances.length > 0) {
                        this.selectInstance(this.instances[0].slug);
                    }
                },

                get filteredInstances() {
                    if (this.visibilityFilter === 'all') return this.instances;
                    return this.instances.filter(i => i.visibility === this.visibilityFilter);
                },
                get filteredConnections() {
                    if (this.visibilityFilter === 'all') return this.connections;
                    return this.connections.filter(c => c.visibility === this.visibilityFilter);
                },
                get filteredKits() {
                    if (this.visibilityFilter === 'all') return this.dataSourceKits;
                    return this.dataSourceKits.filter(k => k.visibility === this.visibilityFilter);
                },
                get filteredInstanceTools() {
                    if (!this.instanceToolFilter) return this.instanceTools;
                    const q = this.instanceToolFilter.toLowerCase();
                    return this.instanceTools.filter(t => (t.name || '').toLowerCase().includes(q) || (t.description || '').toLowerCase().includes(q));
                },
                get availableConnectionsToAttach() {
                    if (!this.currentInstanceDetail) return this.connections;
                    const attachedIds = (this.currentInstanceDetail.connections || []).map(c => c.id);
                    return this.connections.filter(c => !attachedIds.includes(c.id));
                },

                getConnectionIcon(id, type) {
                    if (id.includes('gdrive') || id.includes('drive')) return 'fa-google-drive';
                    if (id.includes('periskope') || id.includes('whatsapp')) return 'fa-whatsapp';
                    if (id.includes('postgres') || id.includes('sql')) return 'fa-database';
                    if (id.includes('fs') || id.includes('file')) return 'fa-folder-open';
                    if (type === 'openapi' || id.includes('api')) return 'fa-network-wired';
                    return 'fa-plug';
                },

                async apiFetch(url, options = {}) {
                    options.headers = options.headers || {};
                    if (this.adminKey) options.headers['X-Central-Admin-Key'] = this.adminKey;
                    if (this.sessionToken) options.headers['X-Central-Session-Token'] = this.sessionToken;
                    try {
                        const res = await fetch(url, options);
                        if (res.status === 401) {
                            this.showAuthModal = true;
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
                    if (this.instances.length > 0) {
                        this.selectInstance(this.instances[0].slug);
                    }
                },

                async fetchMe() {
                    try {
                        const res = await this.apiFetch('/api/v1/auth/me');
                        if (res && res.ok) {
                            this.currentUser = await res.json();
                        }
                    } catch (e) {}
                },

                async refreshAll() {
                    this.loading = true;
                    try {
                        await Promise.all([
                            this.fetchOverview(),
                            this.fetchInstances(),
                            this.fetchConnections(),
                            this.fetchTemplates(),
                            this.fetchDataSourceKits(),
                            this.fetchUsers(),
                            this.fetchRecentLogs()
                        ]);
                        if (this.selectedInstanceSlug) {
                            await this.selectInstance(this.selectedInstanceSlug);
                        }
                    } finally {
                        this.loading = false;
                    }
                },

                async fetchOverview() {
                    try {
                        const res = await this.apiFetch('/api/v1/overview');
                        if (res && res.ok) {
                            this.overview = await res.json();
                            this.toolsTotal = this.overview.total_tools || 0;
                        }
                    } catch (e) {}
                },

                async fetchInstances() {
                    try {
                        const res = await this.apiFetch('/api/v1/instances');
                        if (res && res.ok) {
                            this.instances = await res.json();
                        }
                    } catch (e) {}
                },

                async fetchConnections() {
                    try {
                        const res = await this.apiFetch('/api/v1/connections');
                        if (res && res.ok) {
                            this.connections = await res.json();
                        }
                    } catch (e) {}
                },

                async fetchTemplates() {
                    try {
                        const res = await this.apiFetch('/api/v1/connection-templates');
                        if (res && res.ok) {
                            this.templates = await res.json();
                        }
                    } catch (e) {}
                },

                async fetchDataSourceKits() {
                    try {
                        const res = await this.apiFetch('/api/v1/data-source-kits');
                        if (res && res.ok) {
                            this.dataSourceKits = await res.json();
                        }
                    } catch (e) {}
                },

                async fetchUsers() {
                    try {
                        const res = await this.apiFetch('/api/v1/users');
                        if (res && res.ok) {
                            this.usersList = await res.json();
                        }
                    } catch (e) {}
                },

                async fetchRecentLogs() {
                    try {
                        const res = await this.apiFetch('/api/v1/audit-logs?limit=25');
                        if (res && res.ok) {
                            this.recentLogs = await res.json();
                        }
                    } catch (e) {}
                },

                async selectInstance(slug) {
                    this.selectedInstanceSlug = slug;
                    try {
                        const res = await this.apiFetch(`/api/v1/instances/${slug}`);
                        if (res && res.ok) {
                            this.currentInstanceDetail = await res.json();
                            this.sourcesMapData = this.currentInstanceDetail.sources_map || { organization: 'Epyatis', sources: [] };
                            await Promise.all([
                                this.fetchInstanceTools(slug),
                                this.fetchInstanceLogs(slug)
                            ]);
                        }
                    } catch (e) {}
                },

                async fetchInstanceTools(slug) {
                    try {
                        const res = await this.apiFetch(`/api/v1/instances/${slug}/tools`);
                        if (res && res.ok) {
                            const data = await res.json();
                            this.instanceTools = data.tools || [];
                        }
                    } catch (e) {}
                },

                async fetchInstanceLogs(slug) {
                    try {
                        const res = await this.apiFetch(`/api/v1/instances/${slug}/audit-logs?limit=15`);
                        if (res && res.ok) {
                            this.instanceLogs = await res.json();
                        }
                    } catch (e) {}
                },

                async toggleInstanceTool(slug, toolName) {
                    try {
                        const res = await this.apiFetch(`/api/v1/instances/${slug}/tools/${toolName}/toggle`, { method: 'POST' });
                        if (res && res.ok) {
                            const data = await res.json();
                            const t = this.instanceTools.find(item => item.name === toolName);
                            if (t) t.is_enabled = data.is_enabled;
                            this.showToast(`Ferramenta ${toolName} ${data.is_enabled ? 'ativada' : 'desativada'}.`, 'info');
                        }
                    } catch (e) {
                        this.showToast('Erro ao alternar ferramenta.', 'error');
                    }
                },

                async setInstanceVisibility(slug, newVis) {
                    if (newVis === 'public' && this.currentUser.role !== 'epy_root') {
                        this.showToast('Apenas o Master Admin pode definir instâncias como públicas.', 'error');
                        return;
                    }
                    try {
                        const res = await this.apiFetch(`/api/v1/instances/${slug}`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ visibility: newVis })
                        });
                        if (res && res.ok) {
                            if (this.currentInstanceDetail) this.currentInstanceDetail.visibility = newVis;
                            const inst = this.instances.find(i => i.slug === slug);
                            if (inst) inst.visibility = newVis;
                            this.showToast(`Visibilidade alterada para ${newVis}.`, 'success');
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Falha ao alterar visibilidade.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Erro na requisição.', 'error');
                    }
                },

                async setConnectionVisibility(connId, newVis) {
                    if (newVis === 'public' && this.currentUser.role !== 'epy_root') {
                        this.showToast('Apenas o Master Admin pode definir conexões como públicas.', 'error');
                        return;
                    }
                    try {
                        const res = await this.apiFetch(`/api/v1/connections/${connId}/visibility`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ visibility: newVis })
                        });
                        if (res && res.ok) {
                            const c = this.connections.find(item => item.id === connId);
                            if (c) c.visibility = newVis;
                            this.showToast(`Visibilidade da conexão alterada para ${newVis}.`, 'success');
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Falha ao alterar visibilidade.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Erro na requisição.', 'error');
                    }
                },

                async attachConnection(slug) {
                    if (!this.attachConnectionId) return;
                    try {
                        const res = await this.apiFetch(`/api/v1/instances/${slug}/connections`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ connection_id: this.attachConnectionId })
                        });
                        if (res && res.ok) {
                            this.attachConnectionId = '';
                            this.showToast('Conexão vinculada com sucesso!', 'success');
                            await this.selectInstance(slug);
                            await this.fetchOverview();
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao vincular conexão.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Falha na comunicação com o servidor.', 'error');
                    }
                },

                async detachConnection(slug, connId) {
                    try {
                        const res = await this.apiFetch(`/api/v1/instances/${slug}/connections/${connId}`, {
                            method: 'DELETE'
                        });
                        if (res && res.ok) {
                            this.showToast('Conexão desvinculada da instância.', 'info');
                            await this.selectInstance(slug);
                            await this.fetchOverview();
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao desvincular conexão.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Falha na comunicação.', 'error');
                    }
                },

                async reloadInstance(slug) {
                    try {
                        const res = await this.apiFetch(`/api/v1/instances/${slug}/reload`, { method: 'POST' });
                        if (res && res.ok) {
                            this.showToast('Instância recarregada no Gateway!', 'success');
                            await this.selectInstance(slug);
                        }
                    } catch (e) {
                        this.showToast('Erro ao recarregar instância.', 'error');
                    }
                },

                confirmDeleteInstance(slug) {
                    this.confirmTitle = `Excluir Instância "${slug}"`;
                    this.confirmMessage = 'Tem certeza que deseja excluir esta instância permanentemente? Agentes conectados via este endpoint perderão o acesso.';
                    this.pendingConfirmAction = async () => {
                        const res = await this.apiFetch(`/api/v1/instances/${slug}`, { method: 'DELETE' });
                        if (res && res.ok) {
                            this.showToast('Instância excluída com sucesso.', 'success');
                            this.selectedInstanceSlug = null;
                            this.currentInstanceDetail = null;
                            await this.fetchInstances();
                            if (this.instances.length > 0) this.selectInstance(this.instances[0].slug);
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao excluir.', 'error');
                        }
                    };
                    this.showConfirmModal = true;
                },

                confirmDeleteConnection(connId) {
                    this.confirmTitle = `Excluir Conexão "${connId}"`;
                    this.confirmMessage = 'Tem certeza? Se esta conexão estiver vinculada a instâncias ativas, suas ferramentas serão removidas dos endpoints.';
                    this.pendingConfirmAction = async () => {
                        const res = await this.apiFetch(`/api/v1/connections/${connId}`, { method: 'DELETE' });
                        if (res && res.ok) {
                            this.showToast('Conexão excluída com sucesso.', 'success');
                            await this.refreshAll();
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao excluir conexão.', 'error');
                        }
                    };
                    this.showConfirmModal = true;
                },

                async executeConfirmedAction() {
                    this.showConfirmModal = false;
                    if (this.pendingConfirmAction) {
                        await this.pendingConfirmAction();
                        this.pendingConfirmAction = null;
                    }
                },

                addSourceItem() {
                    if (!this.sourcesMapData.sources) this.sourcesMapData.sources = [];
                    this.sourcesMapData.sources.push({
                        name: 'Nova Fonte',
                        system: 'sistema_custom',
                        content_types: ['documentos'],
                        primary_tools: [],
                        guidance: 'Consulte esta fonte para obter informações sobre...'
                    });
                },

                removeSourceItem(index) {
                    this.sourcesMapData.sources.splice(index, 1);
                },

                async saveStudioSourcesMap() {
                    if (!this.selectedInstanceSlug) return;
                    this.isSavingMap = true;
                    try {
                        const res = await this.apiFetch(`/api/v1/instances/${this.selectedInstanceSlug}/sources-map`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(this.sourcesMapData)
                        });
                        if (res && res.ok) {
                            this.showToast('Mapa de Conhecimento salvo e sincronizado com os Agentes!', 'success');
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao salvar mapa.', 'error');
                        }
                    } finally {
                        this.isSavingMap = false;
                    }
                },

                async loadKitIntoStudioMap(kitId) {
                    if (!kitId || !this.selectedInstanceSlug) return;
                    try {
                        const res = await this.apiFetch(`/api/v1/data-source-kits/${kitId}/apply`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ target_instance_slug: this.selectedInstanceSlug })
                        });
                        if (res && res.ok) {
                            this.showToast('Kit carregado com sucesso na instância!', 'success');
                            await this.selectInstance(this.selectedInstanceSlug);
                        }
                    } catch (e) {
                        this.showToast('Erro ao carregar kit.', 'error');
                    }
                },

                openSaveAsKit(slug) {
                    this.saveKitTargetInstance = slug;
                    this.newKitName = 'Kit ' + (this.currentInstanceDetail ? this.currentInstanceDetail.name : slug);
                    this.showSaveAsKitModal = true;
                },

                async saveKitSubmit() {
                    if (!this.saveKitTargetInstance || !this.newKitName) return;
                    try {
                        const res = await this.apiFetch(`/api/v1/instances/${this.saveKitTargetInstance}/save-as-kit`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                name: this.newKitName,
                                category: this.newKitCategory,
                                description: this.newKitDesc,
                                visibility: 'shared'
                            })
                        });
                        if (res && res.ok) {
                            this.showSaveAsKitModal = false;
                            this.showToast('Kit de Conhecimento salvo com sucesso!', 'success');
                            await this.fetchDataSourceKits();
                        }
                    } catch (e) {
                        this.showToast('Erro ao salvar kit.', 'error');
                    }
                },

                async createInstanceSubmit() {
                    if (!this.newInstanceForm.name || !this.newInstanceForm.slug) {
                        this.showToast('Preencha o nome e o identificador (slug).', 'error');
                        return;
                    }
                    try {
                        const res = await this.apiFetch('/api/v1/instances', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(this.newInstanceForm)
                        });
                        if (res && res.ok) {
                            const data = await res.json();
                            this.showCreateInstanceModal = false;
                            this.showToast(`Instância "${this.newInstanceForm.name}" criada com sucesso!`, 'success');
                            this.newInstanceForm = { name: '', slug: '', description: '', visibility: 'shared' };
                            await this.fetchInstances();
                            this.selectInstance(data.slug);
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao criar instância.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Erro de conexão.', 'error');
                    }
                },

                openTemplateModalWithTarget(slug) {
                    this.templateTargetInstanceSlug = slug || '';
                    this.selectedTemplate = null;
                    this.showTemplateModal = true;
                },

                selectTemplate(t) {
                    this.selectedTemplate = t;
                    this.templateFormValues = {};
                    (t.form_fields || []).forEach(f => {
                        this.templateFormValues[f.id] = f.default || '';
                    });
                    if (this.selectedInstanceSlug && !this.templateTargetInstanceSlug) {
                        this.templateTargetInstanceSlug = this.selectedInstanceSlug;
                    }
                },

                async submitTemplateForm() {
                    if (!this.selectedTemplate) return;
                    try {
                        const res = await this.apiFetch('/api/v1/connections/from-template', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                template_id: this.selectedTemplate.id,
                                form_values: this.templateFormValues,
                                target_instance_slug: this.templateTargetInstanceSlug || 'horst-suite'
                            })
                        });
                        if (res && res.ok) {
                            this.showTemplateModal = false;
                            this.showToast('Serviço conectado com sucesso!', 'success');
                            await this.refreshAll();
                            if (this.templateTargetInstanceSlug) {
                                await this.selectInstance(this.templateTargetInstanceSlug);
                            }
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao instanciar conexão.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Falha ao conectar serviço.', 'error');
                    }
                },

                openSaveAsTemplate(conn) {
                    this.saveTemplateTargetConn = conn;
                    this.newTemplateName = 'Modelo ' + conn.name;
                    this.newTemplateDesc = 'Modelo baseado na conexão ' + conn.id;
                    this.showSaveAsTemplateModal = true;
                },

                async saveConnectionAsTemplateSubmit() {
                    if (!this.saveTemplateTargetConn || !this.newTemplateName) return;
                    try {
                        const res = await this.apiFetch(`/api/v1/connections/${this.saveTemplateTargetConn.id}/save-as-template`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                name: this.newTemplateName,
                                description: this.newTemplateDesc,
                                category: 'Custom',
                                visibility: 'shared'
                            })
                        });
                        if (res && res.ok) {
                            this.showSaveAsTemplateModal = false;
                            this.showToast('Modelo de Conexão salvo com sucesso!', 'success');
                            await this.fetchTemplates();
                        }
                    } catch (e) {
                        this.showToast('Erro ao salvar modelo.', 'error');
                    }
                },

                async discoverTools(connId) {
                    try {
                        const res = await this.apiFetch(`/api/v1/connections/${connId}/discover`, { method: 'POST' });
                        if (res && res.ok) {
                            const data = await res.json();
                            this.showToast(`Redescoberta concluída: ${data.tools_count} ferramentas encontradas.`, 'success');
                            await this.refreshAll();
                        }
                    } catch (e) {
                        this.showToast('Erro ao redescobrir ferramentas.', 'error');
                    }
                },

                async addTokenToCurrentInstance() {
                    if (!this.currentInstanceDetail) return;
                    try {
                        const res = await this.apiFetch(`/api/v1/instances/${this.currentInstanceDetail.id}/tokens`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ label: 'Token Adicional' })
                        });
                        if (res && res.ok) {
                            this.showToast('Novo token gerado com sucesso!', 'success');
                            await this.selectInstance(this.currentInstanceDetail.slug);
                        }
                    } catch (e) {
                        this.showToast('Erro ao gerar token.', 'error');
                    }
                },

                async switchUserAccount(username) {
                    try {
                        const res = await this.apiFetch('/api/v1/auth/switch-user', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ username: username })
                        });
                        if (res && res.ok) {
                            const data = await res.json();
                            this.sessionToken = data.token;
                            localStorage.setItem('central_session_token', data.token);
                            this.showToast(`Sessão alterada para ${username}!`, 'info');
                            await this.fetchMe();
                            await this.refreshAll();
                        }
                    } catch (e) {
                        this.showToast('Erro ao alternar usuário.', 'error');
                    }
                },

                async createUserSubmit() {
                    if (!this.newUserForm.username) return;
                    try {
                        const res = await this.apiFetch('/api/v1/users', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(this.newUserForm)
                        });
                        if (res && res.ok) {
                            this.showCreateUserModal = false;
                            this.showToast(`Usuário ${this.newUserForm.username} criado com sucesso!`, 'success');
                            this.newUserForm = { username: '', display_name: '', role: 'standard' };
                            await this.fetchUsers();
                        }
                    } catch (e) {
                        this.showToast('Erro ao criar usuário.', 'error');
                    }
                },

                async applyKitToPrompt(kitId) {
                    const target = prompt('Informe o slug da instância de destino (ex: horst-suite):', 'horst-suite');
                    if (!target) return;
                    try {
                        const res = await this.apiFetch(`/api/v1/data-source-kits/${kitId}/apply`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ target_instance_slug: target })
                        });
                        if (res && res.ok) {
                            this.showToast(`Kit aplicado na instância ${target}!`, 'success');
                            if (this.selectedInstanceSlug === target) await this.selectInstance(target);
                        }
                    } catch (e) {
                        this.showToast('Erro ao aplicar kit.', 'error');
                    }
                },

                async deleteKit(kitId) {
                    if (!confirm('Deseja realmente excluir este kit?')) return;
                    try {
                        const res = await this.apiFetch(`/api/v1/data-source-kits/${kitId}`, { method: 'DELETE' });
                        if (res && res.ok) {
                            this.showToast('Kit excluído com sucesso.', 'info');
                            await this.fetchDataSourceKits();
                        }
                    } catch (e) {
                        this.showToast('Erro ao excluir kit.', 'error');
                    }
                },

                getEndpointUrl(slug, token) {
                    const loc = window.location;
                    const proto = loc.protocol;
                    const host = loc.host;
                    return `${proto}//${host}/mcp/${slug || 'default'}/sse?token=${token || 'seu_token'}`;
                },

                formatDate(isoString) {
                    if (!isoString) return '-';
                    const d = new Date(isoString);
                    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) + ' (' + d.toLocaleDateString('pt-BR') + ')';
                }
            };
        }
    </script>
</body>
</html>
"""


def get_dashboard_html() -> HTMLResponse:
    return HTMLResponse(content=DASHBOARD_HTML, status_code=200)
