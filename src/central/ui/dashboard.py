"""
Web Dashboard UI para o Epyatis MCP Central.
Interface executiva unificada, aglutinada e centrada em Instâncias e Conexões.
"""

from fastapi.responses import HTMLResponse


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="pt-BR" class="h-full bg-slate-950">
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
        ::-webkit-scrollbar-track { background: #0b0f19; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #475569; }
    </style>
</head>
<body class="h-full flex overflow-hidden text-slate-200 bg-slate-950" x-data="centralApp()" x-init="initApp()" x-cloak>

    <!-- Toast Notifications Container -->
    <div class="fixed top-5 right-5 z-50 flex flex-col gap-2 max-w-sm pointer-events-none">
        <template x-for="t in toasts" :key="t.id">
            <div class="pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg border text-sm font-medium transition-all duration-300 transform translate-y-0"
                 :class="{
                     'bg-emerald-950 border-emerald-700 text-emerald-200': t.type === 'success',
                     'bg-rose-950 border-rose-700 text-rose-200': t.type === 'error',
                     'bg-blue-950 border-blue-700 text-blue-200': t.type === 'info'
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
        <div class="px-4 py-3 bg-slate-950/70 border-b border-slate-800 flex items-center justify-between">
            <div class="flex items-center gap-2.5 overflow-hidden">
                <div class="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 text-xs font-bold shrink-0">
                    <i class="fa-solid fa-user"></i>
                </div>
                <div class="overflow-hidden">
                    <div class="text-xs font-semibold text-slate-100 truncate" x-text="currentUser.display_name || currentUser.username || 'Carregando...'"></div>
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
            <button @click="logout()" class="text-slate-400 hover:text-blue-400 text-xs p-1.5 rounded-lg hover:bg-slate-800 transition-colors" title="Encerrar sessão">
                <i class="fa-solid fa-arrow-right-arrow-left"></i>
            </button>
        </div>

        <!-- Navegação Primária Aglutinada (4 Abas Centrais) -->
        <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            <button @click="switchMainTab('instances')" 
                    :class="activeTab === 'instances' ? 'bg-blue-600 text-white shadow-sm font-semibold' : 'hover:bg-slate-800/70 text-slate-300'"
                    class="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-colors">
                <div class="flex items-center gap-3">
                    <i class="fa-solid fa-cubes-stacked w-4 text-center"></i>
                    <span>Instâncias & Endpoints</span>
                </div>
                <span class="px-1.5 py-0.5 rounded-md text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700/60" x-text="instances.length"></span>
            </button>

            <button @click="switchMainTab('connections')" 
                    :class="activeTab === 'connections' ? 'bg-blue-600 text-white shadow-sm font-semibold' : 'hover:bg-slate-800/70 text-slate-300'"
                    class="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-colors">
                <div class="flex items-center gap-3">
                    <i class="fa-solid fa-plug w-4 text-center"></i>
                    <span>Cofre de Conexões</span>
                </div>
                <span class="px-1.5 py-0.5 rounded-md text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700/60" x-text="connections.length"></span>
            </button>

            <button @click="switchMainTab('kits')" 
                    :class="activeTab === 'kits' ? 'bg-blue-600 text-white shadow-sm font-semibold' : 'hover:bg-slate-800/70 text-slate-300'"
                    class="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-colors">
                <div class="flex items-center gap-3">
                    <i class="fa-solid fa-book-bookmark w-4 text-center"></i>
                    <span>Kits de Conhecimento</span>
                </div>
                <span class="px-1.5 py-0.5 rounded-md text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700/60" x-text="dataSourceKits.length"></span>
            </button>

            <button @click="switchMainTab('governance')" 
                    :class="activeTab === 'governance' ? 'bg-blue-600 text-white shadow-sm font-semibold' : 'hover:bg-slate-800/70 text-slate-300'"
                    class="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-colors">
                <div class="flex items-center gap-3">
                    <i class="fa-solid fa-shield-halved w-4 text-center"></i>
                    <span>Governança & Logs</span>
                </div>
                <span class="w-2 h-2 rounded-full bg-slate-500" :class="overview.total_calls > 0 ? 'bg-emerald-400' : ''"></span>
            </button>
        </nav>

        <!-- Status e Ações Inferiores -->
        <div class="p-4 border-t border-slate-800 bg-slate-950/60 text-[11px] text-slate-400 flex items-center justify-between">
            <div>
                <span class="block text-slate-200 font-semibold" x-text="(toolsTotal || 0) + ' Ferramentas'"></span>
                <span>Porta 8000</span>
            </div>
            <button @click="refreshAll()" :disabled="loading" class="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-750 transition-colors" title="Atualizar dados">
                <i class="fa-solid fa-arrows-rotate" :class="loading ? 'animate-spin' : ''"></i>
            </button>
        </div>
    </aside>

    <!-- Painel de Conteúdo Principal -->
    <main class="flex-1 flex flex-col overflow-hidden bg-slate-950">
        <!-- Topbar com Título e Filtro de Visibilidade -->
        <header class="h-16 bg-slate-900/90 border-b border-slate-800 px-6 flex items-center justify-between shadow-xs shrink-0 backdrop-blur-md">
            <div>
                <h2 class="text-base font-bold text-slate-100" x-text="pageTitles[activeTab] || 'Epyatis MCP Central'"></h2>
                <p class="text-xs text-slate-400" x-text="pageDescriptions[activeTab] || ''"></p>
            </div>

            <!-- Filtros Globais e Ações Rápidas -->
            <div class="flex items-center gap-3">
                <!-- Filtro de Visibilidade -->
                <div class="flex items-center bg-slate-950 p-0.5 rounded-lg border border-slate-700 text-xs font-medium text-slate-400">
                    <button @click="visibilityFilter = 'all'; filterContent()" :class="visibilityFilter === 'all' ? 'bg-slate-800 text-blue-400 border border-slate-700 shadow-xs font-semibold' : 'hover:text-slate-200'" class="px-2.5 py-1 rounded-md transition-all">Todos</button>
                    <button @click="visibilityFilter = 'private'; filterContent()" :class="visibilityFilter === 'private' ? 'bg-slate-800 text-blue-400 border border-slate-700 shadow-xs font-semibold' : 'hover:text-slate-200'" class="px-2.5 py-1 rounded-md transition-all">Privados</button>
                    <button @click="visibilityFilter = 'shared'; filterContent()" :class="visibilityFilter === 'shared' ? 'bg-slate-800 text-blue-400 border border-slate-700 shadow-xs font-semibold' : 'hover:text-slate-200'" class="px-2.5 py-1 rounded-md transition-all">Compartilhados</button>
                    <button @click="visibilityFilter = 'public'; filterContent()" :class="visibilityFilter === 'public' ? 'bg-slate-800 text-blue-400 border border-slate-700 shadow-xs font-semibold' : 'hover:text-slate-200'" class="px-2.5 py-1 rounded-md transition-all">Públicos</button>
                </div>

                <!-- Botões de Ação de Acordo com a Aba -->
                <template x-if="activeTab === 'instances'">
                    <button @click="showCreateInstanceModal = true" class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-colors">
                        <i class="fa-solid fa-plus"></i> Nova Instância
                    </button>
                </template>
                <template x-if="activeTab === 'connections'">
                    <div class="flex items-center gap-2">
                        <button @click="openCreateConnectionModal()" class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-colors" title="Criar conexão direta sem modelo">
                            <i class="fa-solid fa-plus"></i> Nova Conexão Manual
                        </button>
                        <button @click="openCreateTemplateModal()" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors" title="Criar novo modelo do zero">
                            <i class="fa-solid fa-wand-magic-sparkles text-blue-400"></i> Novo Modelo
                        </button>
                        <button @click="showTemplateModal = true" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors" title="Conectar usando catálogo de receitas">
                            <i class="fa-solid fa-bolt text-amber-400"></i> Usar Receita
                        </button>
                    </div>
                </template>
                <template x-if="activeTab === 'kits'">
                    <button @click="openCreateKitModal()" class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-colors">
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
                        <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                            <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Instâncias Disponíveis</span>
                            <span class="text-xs text-slate-500" x-text="filteredInstances.length + ' encontradas'"></span>
                        </div>

                        <div class="space-y-2.5">
                            <template x-for="inst in filteredInstances" :key="inst.id">
                                <div @click="selectInstance(inst.slug)" 
                                     :class="selectedInstanceSlug === inst.slug ? 'ring-2 ring-blue-500 bg-slate-900 border-slate-650 shadow-lg shadow-black/40' : 'bg-slate-900/90 hover:bg-slate-900 border border-slate-750 hover:border-slate-600 shadow-sm'"
                                     class="p-4 rounded-xl cursor-pointer transition-all">
                                    <div class="flex items-start justify-between gap-2">
                                        <div>
                                            <h4 class="text-sm font-bold text-slate-100" x-text="inst.name"></h4>
                                            <span class="text-[11px] font-mono text-slate-400 block mt-0.5" x-text="'slug: ' + inst.slug"></span>
                                        </div>
                                        <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold flex items-center gap-1"
                                              :class="{
                                                  'bg-amber-950/50 text-amber-300 border border-amber-800/60': inst.visibility === 'public',
                                                  'bg-blue-950/50 text-blue-300 border border-blue-800/60': inst.visibility === 'shared',
                                                  'bg-slate-800 text-slate-300 border border-slate-700': inst.visibility === 'private'
                                              }">
                                            <i class="fa-solid" :class="{ 'fa-globe': inst.visibility === 'public', 'fa-users': inst.visibility === 'shared', 'fa-lock': inst.visibility === 'private' }"></i>
                                            <span x-text="inst.visibility === 'public' ? 'Público' : (inst.visibility === 'shared' ? 'Compartilhado' : 'Privado')"></span>
                                        </span>
                                    </div>
                                    <p class="text-xs text-slate-400 mt-2 line-clamp-2" x-text="inst.description || 'Sem descrição cadastrada.'"></p>
                                    
                                    <div class="mt-3 pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                                        <div class="flex items-center gap-3">
                                            <span class="flex items-center gap-1"><i class="fa-solid fa-plug text-[10px] text-slate-500"></i> <strong class="text-slate-200" x-text="(inst.connections || []).length"></strong></span>
                                            <span class="flex items-center gap-1"><i class="fa-solid fa-wrench text-[10px] text-slate-500"></i> <strong class="text-slate-200" x-text="inst.tools_count || 0"></strong></span>
                                        </div>
                                        <button @click.stop="copyText(getEndpointUrl(inst.slug), 'URL do cliente MCP copiada!')"
                                                class="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1 hover:underline">
                                            <i class="fa-regular fa-copy"></i> Copiar URL
                                        </button>
                                    </div>
                                </div>
                            </template>

                            <template x-if="filteredInstances.length === 0">
                                <div class="p-6 text-center bg-slate-900 rounded-xl border border-dashed border-slate-800 text-slate-500 text-xs">
                                    Nenhuma instância encontrada para este filtro.
                                </div>
                            </template>
                        </div>
                    </div>

                    <!-- Coluna da Direita: Studio / Workstation da Instância Selecionada -->
                    <div class="lg:col-span-8">
                        <template x-if="currentInstanceDetail">
                            <div class="bg-slate-900 rounded-xl border border-slate-750 shadow-md shadow-black/30 overflow-hidden">
                                <!-- Cabeçalho do Studio da Instância -->
                                <div class="p-6 border-b border-slate-800 bg-slate-950 text-white">
                                    <div class="flex flex-wrap items-start justify-between gap-4">
                                        <div>
                                            <div class="flex items-center gap-2">
                                                <h3 class="text-lg font-bold text-slate-100" x-text="currentInstanceDetail.name"></h3>
                                                <!-- Dropdown Rápido de Visibilidade com 1 Clique -->
                                                <div class="relative inline-block" x-data="{ openVis: false }">
                                                    <button @click="openVis = !openVis" 
                                                            class="px-2 py-0.5 rounded-full text-[11px] font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
                                                            :class="{
                                                                'bg-amber-950/50 text-amber-300 border border-amber-800/60': currentInstanceDetail.visibility === 'public',
                                                                'bg-blue-950/50 text-blue-300 border border-blue-800/60': currentInstanceDetail.visibility === 'shared',
                                                                'bg-slate-800 text-slate-300 border border-slate-700': currentInstanceDetail.visibility === 'private'
                                                            }">
                                                        <i class="fa-solid" :class="{ 'fa-globe': currentInstanceDetail.visibility === 'public', 'fa-users': currentInstanceDetail.visibility === 'shared', 'fa-lock': currentInstanceDetail.visibility === 'private' }"></i>
                                                        <span x-text="currentInstanceDetail.visibility === 'public' ? 'Público' : (currentInstanceDetail.visibility === 'shared' ? 'Compartilhado' : 'Privado')"></span>
                                                        <i class="fa-solid fa-chevron-down text-[9px] opacity-70"></i>
                                                    </button>
                                                    <div x-show="openVis" @click.outside="openVis = false" 
                                                         class="absolute left-0 mt-1 w-36 bg-slate-850 border border-slate-700 rounded-lg shadow-xl z-20 py-1 text-xs">
                                                        <button @click="setInstanceVisibility(currentInstanceDetail.slug, 'private'); openVis = false" class="w-full text-left px-3 py-1.5 hover:bg-slate-750 text-slate-200 flex items-center gap-2"><i class="fa-solid fa-lock text-slate-400"></i> Privado</button>
                                                        <button @click="setInstanceVisibility(currentInstanceDetail.slug, 'shared'); openVis = false" class="w-full text-left px-3 py-1.5 hover:bg-slate-750 text-blue-300 flex items-center gap-2"><i class="fa-solid fa-users text-blue-400"></i> Compartilhado</button>
                                                        <button @click="setInstanceVisibility(currentInstanceDetail.slug, 'public'); openVis = false" class="w-full text-left px-3 py-1.5 hover:bg-slate-750 text-amber-300 flex items-center gap-2"><i class="fa-solid fa-crown text-amber-400"></i> Público (Root)</button>
                                                    </div>
                                                </div>
                                                <!-- Botão de Configuração de Compartilhamento -->
                                                <template x-if="currentInstanceDetail.visibility === 'shared'">
                                                    <button @click="openShareModal(currentInstanceDetail, 'instance')" 
                                                            class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-950/50 text-blue-300 border border-blue-800/60 hover:bg-blue-900/50 flex items-center gap-1.5 transition-colors cursor-pointer"
                                                            title="Gerenciar usuários com acesso a esta instância">
                                                        <i class="fa-solid fa-user-plus text-[9px]"></i>
                                                        <span x-text="(currentInstanceDetail.shared_user_ids || []).length > 0 ? (currentInstanceDetail.shared_user_ids.length + ' autorizados') : 'Escolher usuários'"></span>
                                                    </button>
                                                </template>
                                            </div>
                                            <p class="text-xs text-slate-400 mt-1" x-text="currentInstanceDetail.description || 'Instância operacional MCP agregadora de ferramentas.'"></p>
                                        </div>

                                        <!-- Ações da Instância -->
                                        <div class="flex items-center gap-2">
                                            <button @click="openEditInstanceModal(currentInstanceDetail)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-blue-400 hover:text-blue-300 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors" title="Editar Nome e Descrição da Instância">
                                                <i class="fa-solid fa-pen-to-square"></i> Editar
                                            </button>
                                            <button @click="reloadInstance(currentInstanceDetail.slug)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors">
                                                <i class="fa-solid fa-rotate text-slate-400"></i> Recarregar
                                            </button>
                                            <button @click="confirmDeleteInstance(currentInstanceDetail.slug)" class="px-3 py-1.5 bg-rose-950/40 hover:bg-rose-900 border border-rose-800 text-rose-300 rounded-lg text-xs font-medium transition-colors" title="Excluir Instância">
                                                <i class="fa-solid fa-trash-can"></i>
                                            </button>
                                        </div>
                                    </div>

                                    <!-- Banner de Conexão Rápida para o Paperclip -->
                                    <div class="mt-4 p-3.5 bg-slate-900/90 rounded-lg border border-slate-750 flex items-center justify-between gap-4">
                                        <div class="overflow-hidden">
                                            <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">URL MCP Server-Sent Events (Paperclip / Claude)</span>
                                            <code class="text-xs text-emerald-400 font-mono truncate block mt-0.5" x-text="getEndpointUrl(currentInstanceDetail.slug)"></code>
                                        </div>
                                        <button @click="copyText(getEndpointUrl(currentInstanceDetail.slug), 'URL do cliente MCP copiada!')"
                                                class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shrink-0 transition-colors flex items-center gap-1.5">
                                            <i class="fa-regular fa-copy"></i> Copiar URL
                                        </button>
                                    </div>
                                </div>

                                <!-- Sub-Abas do Studio da Instância -->
                                <div class="border-b border-slate-800 px-6 flex items-center gap-6 text-xs font-semibold bg-slate-950/60">
                                    <button @click="studioTab = 'connections'" :class="studioTab === 'connections' ? 'text-blue-400 border-b-2 border-blue-500 py-3' : 'text-slate-400 hover:text-slate-200 py-3'">
                                        <i class="fa-solid fa-plug mr-1.5"></i> Conexões Vinculadas (<span x-text="(currentInstanceDetail.connections || []).length"></span>)
                                    </button>
                                    <button @click="studioTab = 'sources_map'" :class="studioTab === 'sources_map' ? 'text-blue-400 border-b-2 border-blue-500 py-3' : 'text-slate-400 hover:text-slate-200 py-3'">
                                        <i class="fa-solid fa-book-atlas mr-1.5"></i> Mapa de Conhecimento
                                    </button>
                                    <button @click="studioTab = 'tools'" :class="studioTab === 'tools' ? 'text-blue-400 border-b-2 border-blue-500 py-3' : 'text-slate-400 hover:text-slate-200 py-3'">
                                        <i class="fa-solid fa-wrench mr-1.5"></i> Ferramentas & Toggles (<span x-text="instanceTools.length"></span>)
                                    </button>
                                    <button @click="studioTab = 'tokens'" :class="studioTab === 'tokens' ? 'text-blue-400 border-b-2 border-blue-500 py-3' : 'text-slate-400 hover:text-slate-200 py-3'">
                                        <i class="fa-solid fa-key mr-1.5"></i> Tokens de Acesso (<span x-text="(currentInstanceDetail.tokens || []).length"></span>)
                                    </button>
                                    <button @click="studioTab = 'logs'" :class="studioTab === 'logs' ? 'text-blue-400 border-b-2 border-blue-500 py-3' : 'text-slate-400 hover:text-slate-200 py-3'">
                                        <i class="fa-solid fa-clock-rotate-left mr-1.5"></i> Auditoria Recente
                                    </button>
                                </div>

                                <!-- Conteúdo da Sub-Aba: Conexões Vinculadas -->
                                <div x-show="studioTab === 'connections'" class="p-6 space-y-4">
                                    <div class="flex items-center justify-between">
                                        <div>
                                            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-300">Serviços e Provedores Conectados</h4>
                                            <p class="text-xs text-slate-400">Conexões ativas agregadas nesta instância.</p>
                                        </div>
                                        <!-- Vincular Conexão Existente ou Criar Nova -->
                                        <div class="flex items-center gap-2">
                                            <div class="flex items-center gap-1.5">
                                                <select x-model="attachConnectionId" class="text-xs border border-slate-700 rounded-lg px-2.5 py-1.5 bg-slate-950 text-slate-200">
                                                    <option value="">Selecione para Vincular...</option>
                                                    <template x-for="c in availableConnectionsToAttach" :key="c.id">
                                                        <option :value="c.id" x-text="c.name + ' (' + c.id + ')'"></option>
                                                    </template>
                                                </select>
                                                <button @click="attachConnection(currentInstanceDetail.slug)" :disabled="!attachConnectionId" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white rounded-lg text-xs font-semibold disabled:opacity-40 transition-colors">
                                                    Vincular
                                                </button>
                                            </div>
                                            <button @click="openCreateConnectionModal(currentInstanceDetail.slug)" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition-colors flex items-center gap-1 shadow-xs" title="Criar nova conexão manual do zero e vincular diretamente a esta instância">
                                                <i class="fa-solid fa-plus text-[10px]"></i> Criar Conexão Manual
                                            </button>
                                            <button @click="openTemplateModalWithTarget(currentInstanceDetail.slug)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1" title="Conectar usando catálogo de receitas pré-configuradas">
                                                <i class="fa-solid fa-wand-magic-sparkles text-blue-400 text-[10px]"></i> Usar Receita
                                            </button>
                                        </div>
                                    </div>

                                    <!-- Lista de Conexões Vinculadas -->
                                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                                        <template x-for="c in currentInstanceDetail.connections" :key="c.id">
                                            <div class="p-3.5 rounded-xl border border-slate-750 bg-slate-950/60 flex items-center justify-between shadow-xs">
                                                <div class="flex items-center gap-3 overflow-hidden">
                                                    <div class="w-9 h-9 rounded-lg bg-blue-950/60 text-blue-400 border border-blue-800/50 flex items-center justify-center font-bold text-xs shrink-0">
                                                        <i class="fa-solid" :class="getConnectionIcon(c.id, c.type)"></i>
                                                    </div>
                                                    <div class="overflow-hidden">
                                                        <h5 class="text-xs font-bold text-slate-200 truncate" x-text="c.name"></h5>
                                                        <span class="text-[11px] text-slate-400 font-mono" x-text="'prefix: ' + (c.prefix || c.id) + '__*'"></span>
                                                    </div>
                                                </div>
                                                <button @click="detachConnection(currentInstanceDetail.slug, c.id)" class="text-slate-400 hover:text-rose-400 text-xs p-1 rounded transition-colors" title="Desvincular desta instância">
                                                    <i class="fa-solid fa-link-slash"></i>
                                                </button>
                                            </div>
                                        </template>

                                        <template x-if="(currentInstanceDetail.connections || []).length === 0">
                                            <div class="col-span-2 p-8 text-center border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
                                                Nenhuma conexão vinculada a esta instância ainda. Use os botões acima para vincular conexões ativas.
                                            </div>
                                        </template>
                                    </div>
                                </div>

                                <!-- Conteúdo da Sub-Aba: Mapa de Conhecimento (Data Sources Map) -->
                                <div x-show="studioTab === 'sources_map'" class="p-6 space-y-4">
                                    <div class="flex items-center justify-between pb-3 border-b border-slate-800">
                                        <div>
                                            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-300">Registro Operacional Nodal de Fontes de Dados</h4>
                                            <p class="text-xs text-slate-400">Catálogo operacional progressivamente descoberto por agentes, com nós independentes, tags e metadados de autoridade.</p>
                                        </div>
                                        <div class="flex items-center gap-2">
                                            <!-- Carregar de Kit -->
                                            <select @change="loadKitIntoStudioMap($event.target.value)" class="text-xs border border-slate-700 rounded-lg px-2 py-1.5 bg-slate-950 text-slate-200">
                                                <option value="">Carregar de um Kit...</option>
                                                <template x-for="k in dataSourceKits" :key="k.id">
                                                    <option :value="k.id" x-text="k.name"></option>
                                                </template>
                                            </select>
                                            <!-- Salvar como Kit -->
                                            <button @click="openSaveAsKit(currentInstanceDetail.slug)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 rounded-lg text-xs font-medium transition-colors">
                                                <i class="fa-solid fa-floppy-disk text-slate-400 mr-1"></i> Salvar como Kit
                                            </button>
                                            <!-- Salvar Alterações -->
                                            <button @click="saveStudioSourcesMap()" :disabled="isSavingMap" class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors flex items-center gap-1.5">
                                                <i class="fa-solid fa-check"></i> <span x-text="isSavingMap ? 'Salvando...' : 'Salvar Alterações'"></span>
                                            </button>
                                        </div>
                                    </div>

                                    <div>
                                        <label class="block text-xs font-medium text-slate-300 mb-1">Nome da Organização / Grupo</label>
                                        <input type="text" x-model="sourcesMapData.organization" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-200 focus:border-blue-500">
                                    </div>

                                    <!-- Lista de Fontes de Dados -->
                                    <div class="space-y-3 pt-2">
                                        <div class="flex items-center justify-between">
                                            <span class="text-xs font-semibold text-slate-300">Fontes Mapeadas (<span x-text="(sourcesMapData.sources || []).length"></span>)</span>
                                            <button @click="addSourceItem()" class="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1">
                                                <i class="fa-solid fa-plus"></i> Adicionar Fonte
                                            </button>
                                        </div>

                                        <template x-for="(s, sIndex) in (sourcesMapData.sources || [])" :key="sIndex">
                                            <div class="p-3.5 rounded-xl border border-slate-750 bg-slate-950/70 space-y-3 relative shadow-xs">
                                                <button @click="removeSourceItem(sIndex)" class="absolute top-3 right-3 text-slate-400 hover:text-rose-400 text-xs p-1" title="Remover Fonte">
                                                    <i class="fa-solid fa-xmark"></i>
                                                </button>
                                                
                                                <div class="grid grid-cols-1 md:grid-cols-3 gap-3 pr-6">
                                                    <div>
                                                        <label class="block text-[10px] font-semibold text-slate-400 uppercase">ID Estável (Node ID)</label>
                                                        <input type="text" x-model="s.id" placeholder="ex: example.procurement.messages.primary" class="w-full text-xs font-mono border border-slate-700 rounded-md p-1.5 bg-slate-900 text-blue-400 focus:border-blue-500">
                                                    </div>
                                                    <div>
                                                        <label class="block text-[10px] font-semibold text-slate-400 uppercase">Nome da Fonte</label>
                                                        <input type="text" x-model="s.name" placeholder="ex: Equipe - Compras (mensagens)" class="w-full text-xs border border-slate-700 rounded-md p-1.5 bg-slate-900 text-slate-200 focus:border-blue-500">
                                                    </div>
                                                    <div>
                                                        <label class="block text-[10px] font-semibold text-slate-400 uppercase">Propósito (Purpose)</label>
                                                        <input type="text" x-model="s.purpose" placeholder="ex: procurement_communications" class="w-full text-xs font-mono border border-slate-700 rounded-md p-1.5 bg-slate-900 text-slate-200 focus:border-blue-500">
                                                    </div>
                                                </div>

                                                <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
                                                    <div>
                                                        <label class="block text-[10px] font-semibold text-slate-400 uppercase">Sistema</label>
                                                        <input type="text" x-model="s.system" placeholder="ex: periskope, gdrive" class="w-full text-xs border border-slate-700 rounded-md p-1.5 bg-slate-900 text-slate-200 focus:border-blue-500">
                                                    </div>
                                                    <div>
                                                        <label class="block text-[10px] font-semibold text-slate-400 uppercase">Autoridade</label>
                                                        <select x-model="s.authority" class="w-full text-xs border border-slate-700 rounded-md p-1.5 bg-slate-900 text-slate-200 focus:border-blue-500">
                                                            <option value="official">Official (SSoT)</option>
                                                            <option value="operational">Operational</option>
                                                            <option value="reference">Reference</option>
                                                            <option value="draft">Draft</option>
                                                        </select>
                                                    </div>
                                                    <div>
                                                        <label class="block text-[10px] font-semibold text-slate-400 uppercase">Status</label>
                                                        <select x-model="s.status" class="w-full text-xs border border-slate-700 rounded-md p-1.5 bg-slate-900 text-slate-200 focus:border-blue-500">
                                                            <option value="active">Active</option>
                                                            <option value="deprecated">Deprecated</option>
                                                            <option value="archived">Archived</option>
                                                        </select>
                                                    </div>
                                                    <div>
                                                        <label class="block text-[10px] font-semibold text-slate-400 uppercase">Tipo de Recurso</label>
                                                        <input type="text" x-model="s.resource_type" placeholder="ex: whatsapp_group, spreadsheet" class="w-full text-xs border border-slate-700 rounded-md p-1.5 bg-slate-900 text-slate-200 focus:border-blue-500">
                                                    </div>
                                                </div>

                                                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                    <div>
                                                        <label class="block text-[10px] font-semibold text-slate-400 uppercase">ID Nativo (Native Resource ID)</label>
                                                        <input type="text" x-model="s.native_resource_id" placeholder="ex: 120363405785055048@g.us ou ID da Planilha" class="w-full text-xs font-mono border border-slate-700 rounded-md p-1.5 bg-slate-900 text-emerald-400 focus:border-blue-500">
                                                    </div>
                                                    <div>
                                                        <div class="flex items-center justify-between mb-1">
                                                            <label class="block text-[10px] font-semibold text-slate-400 uppercase">Tags de Descoberta Operacional</label>
                                                            <span class="text-[10px] text-slate-500">Pressione Enter ou vírgula para adicionar</span>
                                                        </div>
                                                        
                                                        <!-- Container Interativo de Tags (Badges + Input) -->
                                                        <div class="p-2 rounded-lg border border-slate-700 bg-slate-900/90 flex flex-wrap items-center gap-1.5 min-h-[42px] focus-within:border-blue-500">
                                                            <template x-for="(tag, tIdx) in (s.tags || [])" :key="tIdx">
                                                                <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-950/40 border border-amber-800/60 text-amber-300 text-xs font-mono">
                                                                    <span x-text="tag"></span>
                                                                    <button type="button" @click.stop="removeTag(s, tIdx)" class="text-amber-400/70 hover:text-rose-400 ml-0.5 p-0.5 cursor-pointer" title="Remover tag">
                                                                        <i class="fa-solid fa-xmark text-[10px]"></i>
                                                                    </button>
                                                                </span>
                                                            </template>
                                                            
                                                            <input type="text"
                                                                   placeholder="+ Nova tag..."
                                                                   @keydown.enter.prevent="addTagFromInput(s, $event)"
                                                                   @keydown="if ($event.key === ',') { $event.preventDefault(); addTagFromInput(s, $event); }"
                                                                   @blur="addTagFromInput(s, $event)"
                                                                   class="flex-1 min-w-[120px] text-xs bg-transparent text-slate-200 placeholder-slate-500 focus:outline-hidden py-0.5 px-1">
                                                        </div>

                                                        <!-- Sugestões Rápidas de Tags -->
                                                        <div class="mt-1.5 flex flex-wrap items-center gap-1 text-[11px] text-slate-400">
                                                            <span class="text-[10px] text-slate-500 mr-1">Sugestões:</span>
                                                            <template x-for="sug in getSuggestedTags(s)" :key="sug">
                                                                <button type="button" @click="addSuggestedTag(s, sug)" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-slate-600 text-slate-300 text-[10px] font-mono transition-colors">
                                                                    + <span x-text="sug"></span>
                                                                </button>
                                                            </template>
                                                        </div>
                                                    </div>
                                                </div>

                                                <div>
                                                    <label class="block text-[10px] font-semibold text-slate-400 uppercase">Diretriz de Consulta (Guidance para Agentes)</label>
                                                    <textarea x-model="s.guidance" rows="2" placeholder="Instruções claras para os agentes..." class="w-full text-xs border border-slate-700 rounded-md p-1.5 bg-slate-900 text-slate-200 focus:border-blue-500"></textarea>
                                                </div>
                                            </div>
                                        </template>

                                        <template x-if="(sourcesMapData.sources || []).length === 0">
                                            <div class="p-8 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/30">
                                                <i class="fa-solid fa-book-atlas text-2xl text-slate-600 mb-2"></i>
                                                <h4 class="text-sm font-semibold text-slate-300">Nenhuma Fonte Cadastrada nesta Instância</h4>
                                                <p class="text-xs text-slate-500 mt-1 max-w-sm mx-auto">Adicione nós operacionais para guiar os agentes sobre onde localizar cada documento ou grupo.</p>
                                                <button @click="addSourceItem()" class="mt-4 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs inline-flex items-center gap-1.5">
                                                    <i class="fa-solid fa-plus"></i> Adicionar Primeira Fonte
                                                </button>
                                            </div>
                                        </template>
                                    </div>
                                </div>

                                <!-- Conteúdo da Sub-Aba: Ferramentas & Toggles -->
                                <div x-show="studioTab === 'tools'" class="p-6 space-y-4">
                                    <div class="flex items-center justify-between">
                                        <div>
                                            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-300">Ferramentas Agregadas nesta Instância</h4>
                                            <p class="text-xs text-slate-400">Ative ou desative ferramentas instantaneamente para o agente.</p>
                                        </div>
                                        <input type="text" x-model="instanceToolFilter" placeholder="Buscar ferramenta..." class="text-xs border border-slate-700 rounded-lg px-3 py-1.5 w-64 bg-slate-950 text-slate-200 focus:border-blue-500">
                                    </div>

                                    <div class="space-y-2 max-h-96 overflow-y-auto pr-1">
                                        <template x-for="t in filteredInstanceTools" :key="t.id">
                                            <div class="p-3 rounded-xl border border-slate-750 bg-slate-950/60 flex items-center justify-between hover:border-slate-600 transition-colors shadow-xs">
                                                <div class="overflow-hidden pr-4">
                                                    <div class="flex items-center gap-2">
                                                        <code class="text-xs font-mono font-semibold text-blue-400" x-text="t.namespaced_name || t.name"></code>
                                                        <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 font-mono" x-text="t.connection_id"></span>
                                                        <span x-show="t.title && t.title !== (t.namespaced_name || t.name)" class="text-[11px] text-slate-400 truncate max-w-xs" x-text="t.title"></span>
                                                    </div>
                                                    <p class="text-xs text-slate-400 mt-1 line-clamp-1" x-text="t.description || 'Sem descrição.'"></p>
                                                </div>
                                                <!-- Toggle Switch -->
                                                <button @click="toggleInstanceTool(currentInstanceDetail.slug, t)" 
                                                        class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-hidden"
                                                        :class="t.is_enabled ? 'bg-blue-600' : 'bg-slate-800 border border-slate-700'">
                                                    <span class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out"
                                                          :class="t.is_enabled ? 'translate-x-4' : 'translate-x-0'"></span>
                                                </button>
                                            </div>
                                        </template>

                                        <template x-if="filteredInstanceTools.length === 0">
                                            <div class="p-8 text-center text-slate-500 text-xs">
                                                Nenhuma ferramenta encontrada para o filtro atual.
                                            </div>
                                        </template>
                                    </div>
                                </div>

                                <!-- Conteúdo da Sub-Aba: Tokens -->
                                <div x-show="studioTab === 'tokens'" class="p-6 space-y-4">
                                    <div class="flex items-center justify-between">
                                        <div>
                                            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-300">Tokens de Acesso da Instância</h4>
                                            <p class="text-xs text-slate-400">Tokens usados pelo Paperclip ou outros clientes para autenticar nesta instância.</p>
                                        </div>
                                        <button @click="addTokenToCurrentInstance()" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition-colors flex items-center gap-1">
                                            <i class="fa-solid fa-plus text-[10px]"></i> Novo Token
                                        </button>
                                    </div>

                                    <div class="space-y-2">
                                        <template x-for="t in currentInstanceDetail.tokens" :key="t.id">
                                            <div class="p-3 rounded-xl border border-slate-750 bg-slate-950/60 flex items-center justify-between shadow-xs">
                                                <div>
                                                    <span class="text-xs font-semibold text-slate-200 block" x-text="t.label || 'Token'"></span>
                                                    <code class="text-xs font-mono text-emerald-400" x-text="t.token_hint || 'token protegido'"></code>
                                                </div>
                                                <span class="text-[10px] text-slate-500 px-2 py-1">valor exibido somente na emissão</span>
                                            </div>
                                        </template>
                                    </div>
                                </div>

                                <!-- Conteúdo da Sub-Aba: Logs -->
                                <div x-show="studioTab === 'logs'" class="p-6 space-y-3">
                                    <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                                        <span class="text-xs font-bold uppercase tracking-wider text-slate-300">Últimas Execuções da Instância</span>
                                        <button @click="fetchInstanceLogs(currentInstanceDetail.slug)" class="text-xs text-blue-400 hover:underline">Atualizar Logs</button>
                                    </div>
                                    <div class="space-y-1.5 max-h-80 overflow-y-auto">
                                        <template x-for="log in instanceLogs" :key="log.id">
                                            <div class="p-2.5 rounded-lg border border-slate-800 bg-slate-950/60 text-xs flex items-center justify-between">
                                                <div class="flex items-center gap-2">
                                                    <span class="w-2 h-2 rounded-full" :class="log.status === 'success' ? 'bg-emerald-500' : 'bg-rose-500'"></span>
                                                    <code class="font-mono font-bold text-slate-200" x-text="log.tool_name"></code>
                                                </div>
                                                <div class="flex items-center gap-3 text-slate-400 font-mono text-[11px]">
                                                    <span x-text="log.execution_time_ms + 'ms'"></span>
                                                    <span x-text="formatDate(log.timestamp)"></span>
                                                </div>
                                            </div>
                                        </template>
                                        <template x-if="instanceLogs.length === 0">
                                            <div class="p-6 text-center text-slate-500 text-xs">Nenhum log registrado para esta instância recentemente.</div>
                                        </template>
                                    </div>
                                </div>
                            </div>
                        </template>

                        <template x-if="!currentInstanceDetail">
                            <div class="bg-slate-900 rounded-xl border border-dashed border-slate-750 p-12 text-center text-slate-400">
                                <i class="fa-solid fa-hand-pointer text-3xl mb-3 text-slate-600"></i>
                                <h4 class="text-sm font-semibold text-slate-300">Selecione uma Instância</h4>
                                <p class="text-xs mt-1 text-slate-400">Clique em uma instância na coluna ao lado para abrir o Studio e gerenciar suas conexões, diretrizes e ferramentas.</p>
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
                <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div class="flex items-center gap-4 text-xs font-semibold">
                        <button @click="vaultSubTab = 'active'" :class="vaultSubTab === 'active' ? 'text-blue-400 border-b-2 border-blue-500 pb-3' : 'text-slate-400 hover:text-slate-200 pb-3'">
                            <i class="fa-solid fa-link mr-1"></i> Conexões Ativas (<span x-text="connections.length"></span>)
                        </button>
                        <button @click="vaultSubTab = 'templates'" :class="vaultSubTab === 'templates' ? 'text-blue-400 border-b-2 border-blue-500 pb-3' : 'text-slate-400 hover:text-slate-200 pb-3'">
                            <i class="fa-solid fa-wand-magic-sparkles mr-1"></i> Receitas de Conexão (Templates)
                        </button>
                    </div>
                </div>

                <!-- Sub-Aba: Conexões Ativas -->
                <div x-show="vaultSubTab === 'active'" class="space-y-4">
                    <div class="flex items-center justify-between pb-1">
                        <div>
                            <span class="text-xs font-bold uppercase tracking-wider text-slate-300">Conexões Configuradas no Cofre</span>
                            <span class="text-xs text-slate-500 block">Conexões ativas e compartilháveis prontas para acoplamento a qualquer instância</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <button @click="openCreateConnectionModal()" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-colors" title="Criar conexão direta sem modelo pré-existente">
                                <i class="fa-solid fa-plus"></i> Nova Conexão Manual
                            </button>
                            <button @click="showTemplateModal = true" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors" title="Conectar usando receitas prontas">
                                <i class="fa-solid fa-bolt text-amber-400"></i> Usar Receita
                            </button>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <template x-for="c in filteredConnections" :key="c.id">
                            <div class="bg-slate-900 p-5 rounded-xl border border-slate-750 hover:border-slate-600 shadow-sm shadow-black/20 flex flex-col justify-between transition-all">
                                <div>
                                    <div class="flex items-start justify-between gap-2">
                                        <div class="flex items-center gap-3">
                                            <div class="w-10 h-10 rounded-xl bg-blue-950/60 text-blue-400 border border-blue-800/50 flex items-center justify-center text-sm font-bold shrink-0">
                                                <i class="fa-solid" :class="getConnectionIcon(c.id, c.type)"></i>
                                            </div>
                                            <div>
                                                <h4 class="text-sm font-bold text-slate-100" x-text="c.name"></h4>
                                                <span class="text-[11px] font-mono text-slate-400" x-text="'id: ' + c.id"></span>
                                            </div>
                                        </div>
                                        <!-- Visibility Pill com Dropdown Rápido -->
                                        <div class="relative inline-block" x-data="{ openVisConn: false }">
                                            <button @click="openVisConn = !openVisConn" 
                                                    class="px-2 py-0.5 rounded-full text-[10px] font-semibold flex items-center gap-1 cursor-pointer"
                                                    :class="{
                                                        'bg-amber-950/50 text-amber-300 border border-amber-800/60': c.visibility === 'public',
                                                        'bg-blue-950/50 text-blue-300 border border-blue-800/60': c.visibility === 'shared',
                                                        'bg-slate-800 text-slate-300 border border-slate-700': c.visibility === 'private'
                                                    }">
                                                <i class="fa-solid" :class="{ 'fa-globe': c.visibility === 'public', 'fa-users': c.visibility === 'shared', 'fa-lock': c.visibility === 'private' }"></i>
                                                <span x-text="c.visibility === 'public' ? 'Público' : (c.visibility === 'shared' ? 'Compartilhado' : 'Privado')"></span>
                                                <i class="fa-solid fa-chevron-down text-[8px] opacity-60"></i>
                                            </button>
                                            <div x-show="openVisConn" @click.outside="openVisConn = false" class="absolute right-0 mt-1 w-32 bg-slate-850 border border-slate-700 rounded-lg shadow-xl z-20 py-1 text-xs">
                                                <button @click="setConnectionVisibility(c.id, 'private'); openVisConn = false" class="w-full text-left px-3 py-1 hover:bg-slate-750 text-slate-200 flex items-center gap-1.5"><i class="fa-solid fa-lock text-slate-400 text-[10px]"></i> Privado</button>
                                                <button @click="setConnectionVisibility(c.id, 'shared'); openVisConn = false" class="w-full text-left px-3 py-1 hover:bg-slate-750 text-blue-300 flex items-center gap-1.5"><i class="fa-solid fa-users text-blue-400 text-[10px]"></i> Compartilhado</button>
                                                <button @click="setConnectionVisibility(c.id, 'public'); openVisConn = false" class="w-full text-left px-3 py-1 hover:bg-slate-750 text-amber-300 flex items-center gap-1.5"><i class="fa-solid fa-crown text-amber-400 text-[10px]"></i> Público (Root)</button>
                                            </div>
                                        </div>
                                    </div>
                                    <!-- Botão de Configuração de Usuários Compartilhados -->
                                    <template x-if="c.visibility === 'shared'">
                                        <div class="mt-2">
                                            <button @click="openShareModal(c, 'connection')" 
                                                    class="text-[10px] text-blue-300 hover:text-blue-200 font-semibold flex items-center gap-1.5 bg-blue-950/60 px-2 py-0.5 rounded-md border border-blue-800/50 hover:bg-blue-900/50">
                                                <i class="fa-solid fa-user-plus text-[9px]"></i>
                                                <span x-text="(c.shared_user_ids || []).length > 0 ? (c.shared_user_ids.length + ' usuários autorizados') : 'Escolher usuários'"></span>
                                            </button>
                                        </div>
                                    </template>

                                    <div class="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                                        <span class="font-mono text-[11px]" x-text="'prefix: ' + (c.prefix || c.id) + '__*'"></span>
                                        <span class="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-[10px] font-semibold uppercase text-slate-300" x-text="c.type"></span>
                                    </div>
                                </div>

                                <div class="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                                    <div class="flex items-center gap-1.5 flex-wrap">
                                        <button @click="openEditConnectionModal(c)" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-750 border border-slate-700 text-blue-400 hover:text-blue-300 rounded-md font-medium text-[11px] transition-colors" title="Editar Conexão">
                                            <i class="fa-solid fa-pen-to-square mr-1"></i> Editar
                                        </button>
                                        <button @click="discoverTools(c.id)" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-200 rounded-md font-medium text-[11px] transition-colors" title="Redescobrir ferramentas">
                                            <i class="fa-solid fa-arrows-rotate mr-1 text-slate-400"></i> Sync
                                        </button>
                                        <button @click="openSaveAsTemplate(c)" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-200 rounded-md font-medium text-[11px] transition-colors" title="Salvar configuração como modelo">
                                            <i class="fa-solid fa-bookmark mr-1 text-slate-400"></i> Modelo
                                        </button>
                                    </div>
                                    <button @click="confirmDeleteConnection(c.id)" class="text-slate-400 hover:text-rose-400 p-1.5 transition-colors" title="Excluir Conexão">
                                        <i class="fa-solid fa-trash-can text-xs"></i>
                                    </button>
                                </div>
                            </div>
                        </template>
                    </div>
                </div>

                <!-- Sub-Aba: Receitas de Conexão (Templates) -->
                <div x-show="vaultSubTab === 'templates'" class="space-y-4">
                    <div class="flex items-center justify-between pb-1">
                        <div>
                            <span class="text-xs font-bold uppercase tracking-wider text-slate-300">Catálogo de Modelos & Receitas</span>
                            <span class="text-xs text-slate-500 block">Modelos reutilizáveis pré-configurados para conectar serviços com 1 clique ou criar novos modelos</span>
                        </div>
                        <button @click="openCreateTemplateModal()" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-colors" title="Criar novo modelo reutilizável do zero">
                            <i class="fa-solid fa-plus"></i> Novo Modelo do Zero
                        </button>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <template x-for="t in templates" :key="t.id">
                            <div class="bg-slate-900 p-5 rounded-xl border border-slate-750 hover:border-blue-500/80 hover:shadow-lg transition-all flex flex-col justify-between shadow-sm">
                                <div>
                                    <div class="flex items-center gap-3">
                                        <div class="w-10 h-10 rounded-xl bg-blue-950/60 text-blue-400 border border-blue-800/50 flex items-center justify-center text-sm font-bold shrink-0">
                                            <i class="fa-solid" :class="t.icon || 'fa-plug'"></i>
                                        </div>
                                        <div>
                                            <h4 class="text-sm font-bold text-slate-100" x-text="t.name"></h4>
                                            <span class="text-[10px] font-semibold text-blue-400 uppercase" x-text="t.category || 'Conector'"></span>
                                        </div>
                                    </div>
                                    <p class="text-xs text-slate-400 mt-3" x-text="t.description"></p>
                                </div>
                                <div class="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                                    <span class="text-[11px] text-slate-500 font-mono" x-text="'prefix: ' + (t.prefix || 'custom')"></span>
                                    <div class="flex items-center gap-1.5">
                                        <button @click="openEditTemplateModal(t)" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-750 border border-slate-700 text-blue-400 hover:text-blue-300 rounded-md text-[11px] font-medium transition-colors" title="Editar Modelo">
                                            <i class="fa-solid fa-pen-to-square mr-1"></i> Editar
                                        </button>
                                        <button @click="selectTemplate(t)" class="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded-md text-[11px] font-semibold transition-colors flex items-center gap-1 shadow-xs" title="Instanciar conexão a partir deste modelo">
                                            <i class="fa-solid fa-wand-magic-sparkles text-[10px]"></i> Conectar
                                        </button>
                                        <button @click="confirmDeleteTemplate(t)" class="text-slate-400 hover:text-rose-400 p-1 transition-colors" title="Excluir Modelo">
                                            <i class="fa-solid fa-trash-can text-xs"></i>
                                        </button>
                                    </div>
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
                <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                    <div>
                        <h3 class="text-xs font-bold uppercase tracking-wider text-slate-300">Kits de Conhecimento Reutilizáveis</h3>
                        <p class="text-xs text-slate-400">Pacotes prontos de instruções e diretrizes para guiar os agentes em qualquer instância.</p>
                    </div>
                    <button @click="openCreateKitModal()" class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-colors">
                        <i class="fa-solid fa-plus"></i> Novo Kit de Conhecimento
                    </button>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <template x-for="k in filteredKits" :key="k.id">
                        <div class="bg-slate-900 p-5 rounded-xl border border-slate-750 hover:border-slate-600 shadow-sm shadow-black/20 flex flex-col justify-between">
                            <div>
                                <div class="flex items-start justify-between gap-2">
                                    <div>
                                        <h4 class="text-sm font-bold text-slate-100" x-text="k.name"></h4>
                                        <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 font-semibold text-slate-300 uppercase" x-text="k.category || 'Geral'"></span>
                                    </div>
                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold"
                                          :class="k.visibility === 'public' ? 'bg-amber-950/50 text-amber-300 border border-amber-800/60' : 'bg-blue-950/50 text-blue-300 border border-blue-800/60'">
                                        <span x-text="k.visibility === 'public' ? 'Público' : 'Compartilhado'"></span>
                                    </span>
                                </div>
                                <p class="text-xs text-slate-400 mt-2" x-text="k.description || 'Sem descrição.'"></p>
                                <div class="mt-3 text-xs text-slate-400 font-medium">
                                    <i class="fa-solid fa-list-check mr-1 text-slate-500"></i> <span x-text="(k.sources || []).length + ' fontes cadastradas'"></span>
                                </div>
                            </div>

                            <div class="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                                <div class="flex items-center gap-1.5">
                                    <button @click="applyKitToPrompt(k.id)" class="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded-md text-[11px] font-semibold transition-colors flex items-center gap-1 shadow-xs" title="Aplicar este kit na instância">
                                        <i class="fa-solid fa-arrow-right-to-bracket text-[10px]"></i> Aplicar
                                    </button>
                                    <button @click="openEditKitModal(k)" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-750 border border-slate-700 text-blue-400 hover:text-blue-300 rounded-md text-[11px] font-medium transition-colors" title="Editar Kit de Conhecimento">
                                        <i class="fa-solid fa-pen-to-square mr-1"></i> Editar
                                    </button>
                                </div>
                                <button @click="confirmDeleteKit(k)" class="text-slate-400 hover:text-rose-400 p-1.5 text-xs transition-colors" title="Excluir Kit">
                                    <i class="fa-solid fa-trash-can"></i>
                                </button>
                            </div>
                        </div>
                    </template>

                    <template x-if="filteredKits.length === 0">
                        <div class="col-span-full p-8 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/30">
                            <i class="fa-solid fa-book-atlas text-2xl text-slate-600 mb-2"></i>
                            <h4 class="text-sm font-semibold text-slate-300">Nenhum Kit de Conhecimento Cadastrado</h4>
                            <p class="text-xs text-slate-500 mt-1 max-w-sm mx-auto">Crie kits de fontes e diretrizes operacionais para reutilizar entre instâncias.</p>
                            <button @click="openCreateKitModal()" class="mt-4 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs inline-flex items-center gap-1.5">
                                <i class="fa-solid fa-plus"></i> Criar Primeiro Kit
                            </button>
                        </div>
                    </template>
                </div>
            </div>

            <!-- ============================================================= -->
            <!-- ABA 4: GOVERNANÇA, USUÁRIOS & TELEMETRIA                      -->
            <!-- ============================================================= -->
            <div x-show="activeTab === 'governance'" class="space-y-6">
                <div class="flex items-center gap-4 text-xs font-semibold border-b border-slate-800 pb-3">
                    <button @click="govSubTab = 'users'" :class="govSubTab === 'users' ? 'text-blue-400 border-b-2 border-blue-500 pb-3' : 'text-slate-400 hover:text-slate-200 pb-3'">
                        <i class="fa-solid fa-users mr-1"></i> Usuários (<span x-text="usersList.length"></span>)
                    </button>
                    <button @click="govSubTab = 'pending'" :class="govSubTab === 'pending' ? 'text-blue-400 border-b-2 border-blue-500 pb-3' : 'text-slate-400 hover:text-slate-200 pb-3'" class="flex items-center gap-1.5">
                        <i class="fa-solid fa-user-clock mr-1"></i> Aprovações Pendentes
                        <span x-show="pendingUsers.length > 0" class="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500 text-white" x-text="pendingUsers.length"></span>
                    </button>
                    <button @click="govSubTab = 'invites'" :class="govSubTab === 'invites' ? 'text-blue-400 border-b-2 border-blue-500 pb-3' : 'text-slate-400 hover:text-slate-200 pb-3'">
                        <i class="fa-solid fa-ticket mr-1"></i> Convites de Acesso (<span x-text="invitesList.filter(i => !i.is_used).length"></span>)
                    </button>
                    <button @click="govSubTab = 'logs'" :class="govSubTab === 'logs' ? 'text-blue-400 border-b-2 border-blue-500 pb-3' : 'text-slate-400 hover:text-slate-200 pb-3'">
                        <i class="fa-solid fa-list-ul mr-1"></i> Logs de Auditoria Globais
                    </button>
                    <button @click="govSubTab = 'overview'" :class="govSubTab === 'overview' ? 'text-blue-400 border-b-2 border-blue-500 pb-3' : 'text-slate-400 hover:text-slate-200 pb-3'">
                        <i class="fa-solid fa-chart-pie mr-1"></i> Métricas do Sistema
                    </button>
                </div>

                <!-- Sub-Aba: Usuários -->
                <div x-show="govSubTab === 'users'" class="space-y-4">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Usuários Cadastrados</span>
                        <button @click="showCreateUserModal = true" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1">
                            <i class="fa-solid fa-user-plus text-[10px]"></i> Novo Usuário
                        </button>
                    </div>

                    <div class="bg-slate-900 rounded-xl border border-slate-750 shadow-sm overflow-hidden">
                        <table class="w-full text-left text-xs text-slate-300">
                            <thead class="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase text-[10px]">
                                <tr>
                                    <th class="p-3.5">Nome / Usuário</th>
                                    <th class="p-3.5">Função</th>
                                    <th class="p-3.5">Criado Em</th>
                                    <th class="p-3.5 text-right">Ação</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-800/80">
                                <template x-for="u in usersList" :key="u.id">
                                    <tr class="hover:bg-slate-800/40">
                                        <td class="p-3.5">
                                            <span class="font-bold text-slate-100" x-text="u.display_name || u.username"></span>
                                            <span class="text-[11px] text-slate-400 block font-mono" x-text="'@' + u.username"></span>
                                        </td>
                                        <td class="p-3.5">
                                            <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold"
                                                  :class="u.role === 'epy_root' ? 'bg-amber-950/50 text-amber-300 border border-amber-800/60' : 'bg-slate-800 text-slate-300 border border-slate-700'">
                                                <span x-text="u.role === 'epy_root' ? 'Master Admin' : 'Padrão'"></span>
                                            </span>
                                        </td>
                                        <td class="p-3.5 text-slate-400 font-mono" x-text="formatDate(u.created_at)"></td>
                                        <td class="p-3.5 text-right text-xs text-slate-500">Gerenciado por credenciais próprias</td>
                                    </tr>
                                </template>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Sub-Aba: Solicitações de Cadastro Pendentes -->
                <div x-show="govSubTab === 'pending'" class="space-y-4">
                    <div class="flex items-center justify-between">
                        <div>
                            <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Fila de Aprovação de Novos Usuários</span>
                            <p class="text-xs text-slate-500 mt-0.5">Cadastros realizados sem convite necessitam da aprovação do Master Admin.</p>
                        </div>
                        <button @click="fetchPendingUsers()" class="text-xs text-blue-400 hover:underline flex items-center gap-1">
                            <i class="fa-solid fa-rotate text-[10px]"></i> Atualizar Fila
                        </button>
                    </div>

                    <div class="bg-slate-900 rounded-xl border border-slate-750 shadow-sm overflow-hidden">
                        <table class="w-full text-left text-xs text-slate-300">
                            <thead class="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase text-[10px]">
                                <tr>
                                    <th class="p-3.5">Usuário Solicitante</th>
                                    <th class="p-3.5">Nome de Exibição</th>
                                    <th class="p-3.5">Data da Solicitação</th>
                                    <th class="p-3.5 text-right">Decisão</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-800/80">
                                <template x-for="p in pendingUsers" :key="p.id">
                                    <tr class="hover:bg-slate-800/40">
                                        <td class="p-3.5 font-mono font-bold text-slate-100" x-text="'@' + p.username"></td>
                                        <td class="p-3.5 text-slate-300" x-text="p.display_name || '-'"></td>
                                        <td class="p-3.5 text-slate-400 font-mono text-[11px]" x-text="formatDate(p.created_at)"></td>
                                        <td class="p-3.5 text-right space-x-2">
                                            <button @click="approveUser(p.id)" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-xs">
                                                <i class="fa-solid fa-check text-[10px] mr-1"></i> Aprovar
                                            </button>
                                            <button @click="rejectUser(p.id)" class="px-3 py-1 bg-rose-950/60 hover:bg-rose-900 text-rose-300 border border-rose-800 rounded-lg text-xs font-semibold">
                                                <i class="fa-solid fa-xmark text-[10px] mr-1"></i> Rejeitar
                                            </button>
                                        </td>
                                    </tr>
                                </template>
                                <template x-if="pendingUsers.length === 0">
                                    <tr>
                                        <td colspan="4" class="p-8 text-center text-slate-400 text-xs">
                                            <i class="fa-solid fa-circle-check text-emerald-400 text-xl block mb-2"></i>
                                            Nenhuma solicitação de acesso pendente no momento.
                                        </td>
                                    </tr>
                                </template>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Sub-Aba: Convites de Acesso Temporário (Uso Único) -->
                <div x-show="govSubTab === 'invites'" class="space-y-4">
                    <div class="flex flex-wrap items-center justify-between gap-3 bg-slate-900 p-4 rounded-xl border border-slate-750 shadow-sm">
                        <div>
                            <span class="text-xs font-bold uppercase tracking-wider text-slate-300 block">Gerador de Convites de Uso Único</span>
                            <p class="text-xs text-slate-400">Usuários que se cadastram via link/código de convite são ativados instantaneamente.</p>
                        </div>
                        <div class="flex items-center gap-2">
                            <select x-model="inviteHours" class="text-xs border border-slate-700 rounded-lg px-2.5 py-1.5 bg-slate-950 text-slate-200">
                                <option value="12">Válido por 12 horas</option>
                                <option value="24">Válido por 24 horas</option>
                                <option value="48">Válido por 48 horas</option>
                                <option value="168">Válido por 7 dias</option>
                            </select>
                            <button @click="generateInvite()" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs">
                                <i class="fa-solid fa-plus text-[10px]"></i> Gerar Convite
                            </button>
                        </div>
                    </div>

                    <div class="bg-slate-900 rounded-xl border border-slate-750 shadow-sm overflow-hidden">
                        <table class="w-full text-left text-xs text-slate-300">
                            <thead class="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase text-[10px]">
                                <tr>
                                    <th class="p-3.5">Código do Convite</th>
                                    <th class="p-3.5">Expira em</th>
                                    <th class="p-3.5">Status</th>
                                    <th class="p-3.5">Utilizado Por</th>
                                    <th class="p-3.5 text-right">Ações</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-800/80">
                                <template x-for="inv in invitesList" :key="inv.id">
                                    <tr class="hover:bg-slate-800/40">
                                        <td class="p-3.5 font-mono font-bold text-slate-100">
                                            <span class="bg-slate-950 border border-slate-800 px-2 py-1 rounded text-blue-400 select-all" x-text="inv.code"></span>
                                        </td>
                                        <td class="p-3.5 font-mono text-[11px] text-slate-400" x-text="formatDate(inv.expires_at)"></td>
                                        <td class="p-3.5">
                                            <template x-if="inv.is_used">
                                                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700">Utilizado</span>
                                            </template>
                                            <template x-if="!inv.is_used">
                                                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950/50 text-emerald-300 border border-emerald-800/60">Disponível</span>
                                            </template>
                                        </td>
                                        <td class="p-3.5 font-mono text-slate-300" x-text="inv.used_by ? ('@' + inv.used_by) : '-'"></td>
                                        <td class="p-3.5 text-right space-x-2">
                                            <template x-if="!inv.is_used">
                                                <button @click="copyText(window.location.origin + '/?invite=' + inv.code, 'Link de cadastro copiado!')" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-200 rounded text-xs font-semibold">
                                                    <i class="fa-regular fa-copy text-[10px] mr-1"></i> Copiar Link
                                                </button>
                                            </template>
                                            <template x-if="!inv.is_used">
                                                <button @click="deleteInvite(inv.code)" class="p-1 text-slate-400 hover:text-rose-400 text-xs" title="Revogar Convite">
                                                    <i class="fa-solid fa-trash-can"></i>
                                                </button>
                                            </template>
                                        </td>
                                    </tr>
                                </template>
                                <template x-if="invitesList.length === 0">
                                    <tr>
                                        <td colspan="5" class="p-8 text-center text-slate-500 text-xs">Nenhum convite gerado recentemente.</td>
                                    </tr>
                                </template>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Sub-Aba: Logs Globais -->
                <div x-show="govSubTab === 'logs'" class="space-y-3">
                    <div class="bg-slate-900 rounded-xl border border-slate-750 shadow-sm overflow-hidden">
                        <table class="w-full text-left text-xs text-slate-300">
                            <thead class="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase text-[10px]">
                                <tr>
                                    <th class="p-3.5">Status</th>
                                    <th class="p-3.5">Instância</th>
                                    <th class="p-3.5">Ferramenta</th>
                                    <th class="p-3.5">Latência</th>
                                    <th class="p-3.5">Timestamp</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-800/80">
                                <template x-for="l in recentLogs" :key="l.id">
                                    <tr class="hover:bg-slate-800/40">
                                        <td class="p-3.5">
                                            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold"
                                                  :class="l.status === 'success' ? 'bg-emerald-950/50 text-emerald-300 border border-emerald-800/60' : 'bg-rose-950/50 text-rose-300 border border-rose-800/60'"
                                                  x-text="l.status"></span>
                                        </td>
                                        <td class="p-3.5 font-mono text-slate-300" x-text="l.instance_slug || '-'"></td>
                                        <td class="p-3.5 font-mono font-semibold text-blue-400" x-text="l.tool_name"></td>
                                        <td class="p-3.5 font-mono text-slate-400" x-text="l.execution_time_ms + ' ms'"></td>
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
                        <div class="bg-slate-900 p-5 rounded-xl border border-slate-750 shadow-sm">
                            <span class="text-xs text-slate-400 font-medium">Instâncias Ativas</span>
                            <div class="text-2xl font-bold text-slate-100 mt-1" x-text="overview.active_instances || 0"></div>
                        </div>
                        <div class="bg-slate-900 p-5 rounded-xl border border-slate-750 shadow-sm">
                            <span class="text-xs text-slate-400 font-medium">Conexões Upstream</span>
                            <div class="text-2xl font-bold text-slate-100 mt-1" x-text="overview.total_connections || 0"></div>
                        </div>
                        <div class="bg-slate-900 p-5 rounded-xl border border-slate-750 shadow-sm">
                            <span class="text-xs text-slate-400 font-medium">Total de Ferramentas</span>
                            <div class="text-2xl font-bold text-slate-100 mt-1" x-text="overview.total_tools || 0"></div>
                        </div>
                        <div class="bg-slate-900 p-5 rounded-xl border border-slate-750 shadow-sm">
                            <span class="text-xs text-slate-400 font-medium">Taxa de Sucesso</span>
                            <div class="text-2xl font-bold text-emerald-400 mt-1" x-text="(overview.success_rate || 100) + '%'"></div>
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
    <div x-show="showCreateInstanceModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4" @click.self="showCreateInstanceModal = false">
        <div class="bg-slate-900 rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-750 text-slate-100 space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                <h3 class="text-sm font-bold text-slate-100 flex items-center gap-2">
                    <i class="fa-solid fa-cubes-stacked text-blue-500"></i> Criar Nova Instância MCP
                </h3>
                <button @click="showCreateInstanceModal = false" class="text-slate-400 hover:text-slate-200"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Nome da Instância</label>
                    <input type="text" x-model="newInstanceForm.name" placeholder="Ex: Finance Operational Suite" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Identificador de URL (Slug)</label>
                    <input type="text" x-model="newInstanceForm.slug" placeholder="Ex: finance-suite" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 font-mono bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Descrição</label>
                    <textarea x-model="newInstanceForm.description" rows="2" placeholder="Finalidade deste endpoint para os agentes..." class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-blue-500"></textarea>
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Visibilidade</label>
                    <select x-model="newInstanceForm.visibility" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                        <option value="private">Privado (Somente Você)</option>
                        <option value="shared">Compartilhado (Equipe)</option>
                        <option value="public" :disabled="currentUser.role !== 'epy_root'">Público (Requer Master Admin)</option>
                    </select>
                </div>
            </div>
            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button @click="showCreateInstanceModal = false" class="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg">Cancelar</button>
                <button @click="createInstanceSubmit()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs">Criar Instância</button>
            </div>
        </div>
    </div>

    <!-- Modal 2: Wizard de Template / Nova Conexão -->
    <div x-show="showTemplateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4" @click.self="showTemplateModal = false">
        <div class="bg-slate-900 rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-750 text-slate-100 space-y-4 max-h-[90vh] overflow-y-auto">
            <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                <h3 class="text-sm font-bold text-slate-100 flex items-center gap-2">
                    <i class="fa-solid fa-wand-magic-sparkles text-blue-500"></i>
                    <span x-text="selectedTemplate ? 'Conectar: ' + selectedTemplate.name : 'Conectar Novo Serviço'"></span>
                </h3>
                <button @click="showTemplateModal = false" class="text-slate-400 hover:text-slate-200"><i class="fa-solid fa-xmark"></i></button>
            </div>

            <!-- Se nenhum template selecionado, mostra lista rápida -->
            <template x-if="!selectedTemplate">
                <div class="space-y-2">
                    <p class="text-xs text-slate-400">Escolha uma receita para iniciar o assistente guiado:</p>
                    <div class="grid grid-cols-1 gap-2">
                        <template x-for="t in templates" :key="t.id">
                            <div @click="selectTemplate(t)" class="p-3 rounded-xl border border-slate-750 bg-slate-950/60 hover:border-blue-500 hover:bg-blue-950/20 cursor-pointer flex items-center justify-between transition-all">
                                <div class="flex items-center gap-3">
                                    <i class="fa-solid text-blue-400" :class="t.icon || 'fa-plug'"></i>
                                    <div>
                                        <div class="text-xs font-bold text-slate-100" x-text="t.name"></div>
                                        <div class="text-[11px] text-slate-400" x-text="t.description"></div>
                                    </div>
                                </div>
                                <i class="fa-solid fa-chevron-right text-xs text-slate-500"></i>
                            </div>
                        </template>
                    </div>
                </div>
            </template>

            <!-- Formulário Dinâmico do Template Selecionado -->
            <template x-if="selectedTemplate">
                <div class="space-y-3">
                    <p class="text-xs text-slate-400" x-text="selectedTemplate.description"></p>
                    <template x-for="field in (selectedTemplate.form_fields || [])" :key="field.id">
                        <div>
                            <label class="block text-xs font-medium text-slate-300 mb-1" x-text="field.label + (field.required ? ' *' : '')"></label>
                            <input :type="field.type === 'password' ? 'password' : 'text'" 
                                   x-model="templateFormValues[field.id]" 
                                   :placeholder="field.description || ''" 
                                   class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-blue-500">
                        </div>
                    </template>
                    <div class="pt-2">
                        <label class="block text-xs font-medium text-slate-300 mb-1">Vincular diretamente à Instância</label>
                        <select x-model="templateTargetInstanceSlug" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                            <option value="">Não vincular agora (deixar no cofre)</option>
                            <template x-for="inst in instances" :key="inst.slug">
                                <option :value="inst.slug" x-text="inst.name + ' (' + inst.slug + ')'"></option>
                            </template>
                        </select>
                    </div>
                </div>
            </template>

            <div class="flex items-center justify-between pt-3 border-t border-slate-800">
                <button @click="selectedTemplate ? (selectedTemplate = null) : (showTemplateModal = false)" class="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg">
                    <span x-text="selectedTemplate ? 'Voltar' : 'Cancelar'"></span>
                </button>
                <template x-if="selectedTemplate">
                    <button @click="submitTemplateForm()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs">Concluir Conexão</button>
                </template>
            </div>
        </div>
    </div>

    <!-- Modal 3: Troca Rápida de Usuário & Sessão -->
    <!-- Modal 4: Criar Novo Usuário -->
    <div x-show="showCreateUserModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4" @click.self="showCreateUserModal = false">
        <div class="bg-slate-900 rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-750 text-slate-100 space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                <h3 class="text-sm font-bold text-slate-100 flex items-center gap-2">
                    <i class="fa-solid fa-user-plus text-blue-500"></i> Criar Novo Usuário
                </h3>
                <button @click="showCreateUserModal = false" class="text-slate-400 hover:text-slate-200"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Nome de Exibição</label>
                    <input type="text" x-model="newUserForm.display_name" placeholder="Ex: Analista de Operações" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Username (Login)</label>
                    <input type="text" x-model="newUserForm.username" placeholder="Ex: analista_ops" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 font-mono bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Função / Perfil</label>
                    <select x-model="newUserForm.role" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                        <option value="standard">Padrão</option>
                        <option value="epy_root">Master Admin</option>
                    </select>
                </div>
            </div>
            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button @click="showCreateUserModal = false" class="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg">Cancelar</button>
                <button @click="createUserSubmit()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs">Salvar</button>
            </div>
        </div>
    </div>

    <!-- Modal 5: Salvar como Template -->
    <div x-show="showSaveAsTemplateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4" @click.self="showSaveAsTemplateModal = false">
        <div class="bg-slate-900 rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-750 text-slate-100 space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                <h3 class="text-sm font-bold text-slate-100">Salvar Conexão como Modelo Reutilizável</h3>
                <button @click="showSaveAsTemplateModal = false" class="text-slate-400 hover:text-slate-200"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Nome do Modelo</label>
                    <input type="text" x-model="newTemplateName" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Descrição</label>
                    <textarea x-model="newTemplateDesc" rows="2" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-blue-500"></textarea>
                </div>
            </div>
            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button @click="showSaveAsTemplateModal = false" class="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg">Cancelar</button>
                <button @click="saveConnectionAsTemplateSubmit()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs">Salvar Modelo</button>
            </div>
        </div>
    </div>

    <!-- Modal 6: Salvar como Kit -->
    <div x-show="showSaveAsKitModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4" @click.self="showSaveAsKitModal = false">
        <div class="bg-slate-900 rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-750 text-slate-100 space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                <h3 class="text-sm font-bold text-slate-100">Salvar Mapa como Kit de Conhecimento</h3>
                <button @click="showSaveAsKitModal = false" class="text-slate-400 hover:text-slate-200"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Nome do Kit</label>
                    <input type="text" x-model="newKitName" placeholder="Ex: Kit Operacional Padrão" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Categoria</label>
                    <input type="text" x-model="newKitCategory" placeholder="Ex: Operações, Finanças" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Descrição</label>
                    <textarea x-model="newKitDesc" rows="2" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-blue-500"></textarea>
                </div>
            </div>
            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button @click="showSaveAsKitModal = false" class="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg">Cancelar</button>
                <button @click="saveKitSubmit()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs">Salvar Kit</button>
            </div>
        </div>
    </div>

    <!-- Modal 7: Confirmação Segura de Exclusão -->
    <div x-show="showConfirmModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4" @click.self="showConfirmModal = false">
        <div class="bg-slate-900 rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-750 text-slate-100 space-y-4">
            <div class="flex items-center gap-3 text-rose-500">
                <div class="w-10 h-10 rounded-full bg-rose-950/60 border border-rose-800 flex items-center justify-center text-rose-400 text-lg shrink-0">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                </div>
                <div>
                    <h3 class="text-sm font-bold text-slate-100" x-text="confirmTitle"></h3>
                    <p class="text-xs text-slate-400 mt-0.5" x-text="confirmMessage"></p>
                </div>
            </div>
            <div class="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button @click="showConfirmModal = false" class="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg">Cancelar</button>
                <button @click="executeConfirmedAction()" class="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold shadow-xs">Confirmar Exclusão</button>
            </div>
        </div>
    </div>

    <!-- Modal: Compartilhamento Granular de Recursos -->
    <div x-show="showShareModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4" @click.self="showShareModal = false">
        <div class="bg-slate-900 rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-750 text-slate-100 space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                <div>
                    <h3 class="text-sm font-bold text-slate-100 flex items-center gap-2">
                        <i class="fa-solid fa-user-group text-blue-500"></i> Compartilhar <span x-text="shareTargetType === 'connection' ? 'Conexão' : 'Instância'"></span>
                    </h3>
                    <p class="text-xs text-slate-400 font-medium" x-text="shareTargetName"></p>
                </div>
                <button @click="showShareModal = false" class="text-slate-400 hover:text-slate-200"><i class="fa-solid fa-xmark"></i></button>
            </div>

            <div class="space-y-3">
                <p class="text-xs text-slate-400">Selecione quais usuários terão permissão de acesso a este recurso quando a visibilidade for definida como <span class="font-bold text-blue-400">Compartilhado</span>.</p>
                
                <input type="text" x-model="shareSearchQuery" placeholder="Buscar usuário por nome..." class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-blue-500">

                <div class="max-h-60 overflow-y-auto space-y-1.5 border border-slate-800 rounded-xl p-2 bg-slate-950/60">
                    <template x-for="u in filteredShareUsers" :key="u.id">
                        <label class="flex items-center justify-between p-2.5 rounded-lg hover:bg-slate-800/60 cursor-pointer border border-transparent hover:border-slate-700 transition-all">
                            <div class="flex items-center gap-3">
                                <input type="checkbox" :value="u.id" x-model="shareSelectedUserIds" class="rounded border-slate-700 bg-slate-900 text-blue-600 focus:ring-blue-500">
                                <div>
                                    <span class="text-xs font-bold text-slate-100 block" x-text="u.display_name || u.username"></span>
                                    <span class="text-[11px] text-slate-400 font-mono" x-text="'@' + u.username"></span>
                                </div>
                            </div>
                            <span class="text-[10px] px-2 py-0.5 rounded-full font-semibold"
                                  :class="u.role === 'epy_root' ? 'bg-amber-950/50 text-amber-300 border border-amber-800/60' : 'bg-slate-800 text-slate-300 border border-slate-700'"
                                  x-text="u.role === 'epy_root' ? 'Master Admin' : 'Padrão'"></span>
                        </label>
                    </template>
                </div>
            </div>

            <div class="flex items-center justify-between pt-3 border-t border-slate-800">
                <span class="text-xs text-slate-400 font-medium"><span x-text="shareSelectedUserIds.length"></span> selecionado(s)</span>
                <div class="flex items-center gap-2">
                    <button @click="showShareModal = false" class="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg">Cancelar</button>
                    <button @click="saveShares()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs">Salvar Compartilhamento</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal 8: Autenticação, Login & Cadastro Integrado -->
    <div x-show="showAuthModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4" @click.self="if (currentUser.username) showAuthModal = false">
        <div class="bg-slate-900 rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-750 text-slate-100 space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                <div class="flex items-center gap-2">
                    <div class="w-7 h-7 rounded-lg bg-blue-950/60 text-blue-400 border border-blue-800/50 flex items-center justify-center text-xs font-bold">
                        <i class="fa-solid fa-shield-halved"></i>
                    </div>
                    <h3 class="text-sm font-bold text-slate-100">Autenticação & Contas</h3>
                </div>
                <template x-if="currentUser.username">
                    <button @click="showAuthModal = false" class="text-slate-400 hover:text-slate-200"><i class="fa-solid fa-xmark"></i></button>
                </template>
            </div>

            <!-- Abas do Modal de Auth -->
            <div class="flex items-center rounded-xl bg-slate-950 border border-slate-800 p-1 text-xs font-semibold">
                <button @click="authTab = 'login'" :class="authTab === 'login' ? 'bg-slate-800 text-slate-100 shadow-xs' : 'text-slate-400 hover:text-slate-200'" class="flex-1 py-1.5 rounded-lg transition-all text-center">
                    Entrar
                </button>
                <button @click="authTab = 'register'" :class="authTab === 'register' ? 'bg-slate-800 text-slate-100 shadow-xs' : 'text-slate-400 hover:text-slate-200'" class="flex-1 py-1.5 rounded-lg transition-all text-center">
                    Criar Conta
                </button>
            </div>

            <!-- Aba 1: Entrar (Login) -->
            <div x-show="authTab === 'login'" class="space-y-3">
                <template x-if="!useAdminKeyLogin">
                    <div class="space-y-3">
                        <div>
                            <label class="block text-xs font-medium text-slate-300 mb-1">Nome de Usuário</label>
                            <input type="text" x-model="loginForm.username" placeholder="Seu usuário..." class="w-full text-xs border border-slate-700 rounded-lg p-2.5 font-mono bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-blue-500">
                        </div>
                        <div>
                            <label class="block text-xs font-medium text-slate-300 mb-1">Senha</label>
                            <input type="password" x-model="loginForm.password" placeholder="Sua senha..." class="w-full text-xs border border-slate-700 rounded-lg p-2.5 font-mono bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-blue-500" @keyup.enter="submitLogin()">
                        </div>
                        <button @click="submitLogin()" class="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors">
                            Entrar no Sistema
                        </button>
                    </div>
                </template>

                <template x-if="useAdminKeyLogin">
                    <div class="space-y-3">
                        <div>
                            <label class="block text-xs font-medium text-slate-300 mb-1">Chave Mestra Admin (Master Key)</label>
                            <input type="password" x-model="authKeyInput" placeholder="Chave de Admin..." class="w-full text-xs border border-slate-700 rounded-lg p-2.5 text-center font-mono bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-amber-500" @keyup.enter="saveAdminKey()">
                        </div>
                        <button @click="saveAdminKey()" class="w-full py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors">
                            Acessar como Master Admin
                        </button>
                    </div>
                </template>

                <div class="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px]">
                    <button @click="useAdminKeyLogin = !useAdminKeyLogin" class="text-blue-400 hover:underline">
                        <span x-text="useAdminKeyLogin ? '← Entrar com Usuário e Senha' : '🔑 Entrar com Chave Mestra'"></span>
                    </button>
                </div>
            </div>

            <!-- Aba 2: Criar Nova Conta -->
            <div x-show="authTab === 'register'" class="space-y-3 text-left">
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Nome de Usuário *</label>
                    <input type="text" x-model="registerForm.username" placeholder="Ex: analista_ops" class="w-full text-xs border border-slate-700 rounded-lg p-2 font-mono bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Nome de Exibição</label>
                    <input type="text" x-model="registerForm.display_name" placeholder="Ex: João Silva" class="w-full text-xs border border-slate-700 rounded-lg p-2 bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Senha (Mínimo 6 caracteres) *</label>
                    <input type="password" x-model="registerForm.password" placeholder="Senha segura..." class="w-full text-xs border border-slate-700 rounded-lg p-2 font-mono bg-slate-950 text-slate-100 placeholder-slate-500 focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Código de Convite (Opcional)</label>
                    <input type="text" x-model="registerForm.invite_code" placeholder="Código fornecido pelo Admin..." class="w-full text-xs border border-slate-700 rounded-lg p-2 font-mono bg-slate-950 text-amber-300 placeholder-slate-500 focus:border-blue-500">
                    <p class="text-[10px] text-slate-400 mt-1">
                        💡 Com convite: liberação imediata. Sem convite: aguarda aprovação do Master Admin.
                    </p>
                </div>
                <button @click="submitRegister()" class="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors">
                    Solicitar Cadastro
                </button>
            </div>

            <template x-if="currentUser.username">
                <div class="pt-2 border-t border-slate-800 flex items-center justify-between">
                    <span class="text-xs text-slate-400">Logado como: <strong class="text-slate-200 font-mono" x-text="'@' + currentUser.username"></strong></span>
                    <button @click="logout()" class="text-xs text-rose-400 hover:text-rose-300 font-semibold flex items-center gap-1">
                        <i class="fa-solid fa-arrow-right-from-bracket text-[10px]"></i> Sair
                    </button>
                </div>
            </template>
        </div>
    </div>

    <!-- Modal: Editar Conexão -->
    <div x-show="showEditConnectionModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4" @click.self="showEditConnectionModal = false">
        <div class="bg-slate-900 rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-750 text-slate-100 space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                <h3 class="text-sm font-bold text-slate-100 flex items-center gap-2">
                    <i class="fa-solid fa-pen-to-square text-blue-400"></i> Editar Conexão
                </h3>
                <button @click="showEditConnectionModal = false" class="text-slate-400 hover:text-slate-200"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-3 max-h-[70vh] overflow-y-auto pr-1">
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">ID da Conexão (Fixo)</label>
                        <input type="text" x-model="editConnectionForm.id" disabled class="w-full text-xs border border-slate-800 rounded-lg p-2.5 font-mono bg-slate-950/50 text-slate-400 cursor-not-allowed">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Prefixo de Ferramentas</label>
                        <input type="text" x-model="editConnectionForm.prefix" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 font-mono bg-slate-950 text-slate-100 focus:border-blue-500">
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Nome Amigável</label>
                    <input type="text" x-model="editConnectionForm.name" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                </div>
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Tipo de Conexão</label>
                        <select x-model="editConnectionForm.type" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                            <option value="stdio">stdio (Local CLI/Process)</option>
                            <option value="remote_mcp">remote_mcp (SSE Endpoint)</option>
                            <option value="openapi">openapi (REST API)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Visibilidade</label>
                        <select x-model="editConnectionForm.visibility" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                            <option value="private">Privado</option>
                            <option value="shared">Compartilhado</option>
                            <option value="public" x-show="currentUser.role === 'epy_root'">Público (Root)</option>
                        </select>
                    </div>
                </div>
                <template x-if="editConnectionForm.type === 'stdio'">
                    <div class="space-y-3">
                        <div>
                            <label class="block text-xs font-medium text-slate-300 mb-1">Comando Executável</label>
                            <input type="text" x-model="editConnectionForm.command" placeholder="Ex: npx, python, uvx" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 font-mono bg-slate-950 text-slate-100 focus:border-blue-500">
                        </div>
                        <div>
                            <label class="block text-xs font-medium text-slate-300 mb-1">Argumentos (Separados por espaço)</label>
                            <input type="text" x-model="editConnectionForm.argsText" placeholder="Ex: -y @us-all/google-drive-mcp" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 font-mono bg-slate-950 text-slate-100 focus:border-blue-500">
                        </div>
                        <div>
                            <label class="block text-xs font-medium text-slate-300 mb-1">Variáveis de Ambiente (JSON)</label>
                            <textarea x-model="editConnectionForm.envText" rows="3" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 font-mono bg-slate-950 text-slate-100 focus:border-blue-500"></textarea>
                        </div>
                    </div>
                </template>
                <template x-if="editConnectionForm.type === 'remote_mcp' || editConnectionForm.type === 'openapi'">
                    <div class="space-y-3">
                        <div>
                            <label class="block text-xs font-medium text-slate-300 mb-1">URL do Endpoint</label>
                            <input type="text" x-model="editConnectionForm.url" placeholder="https://api.exemplo.com/mcp" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 font-mono bg-slate-950 text-slate-100 focus:border-blue-500">
                        </div>
                        <div>
                            <label class="block text-xs font-medium text-slate-300 mb-1">Configurações de Auth / Headers (JSON)</label>
                            <textarea x-model="editConnectionForm.authConfigText" rows="3" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 font-mono bg-slate-950 text-slate-100 focus:border-blue-500"></textarea>
                        </div>
                    </div>
                </template>
            </div>
            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button @click="showEditConnectionModal = false" class="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg">Cancelar</button>
                <button @click="saveEditedConnection()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs">Salvar Alterações</button>
            </div>
        </div>
    </div>

    <!-- Modal: Editar Modelo de Conexão -->
    <div x-show="showEditTemplateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4" @click.self="showEditTemplateModal = false">
        <div class="bg-slate-900 rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-750 text-slate-100 space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                <h3 class="text-sm font-bold text-slate-100 flex items-center gap-2">
                    <i class="fa-solid fa-wand-magic-sparkles text-blue-400"></i> Editar Modelo de Conexão
                </h3>
                <button @click="showEditTemplateModal = false" class="text-slate-400 hover:text-slate-200"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-3 max-h-[70vh] overflow-y-auto pr-1">
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Nome do Modelo</label>
                    <input type="text" x-model="editTemplateForm.name" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Descrição</label>
                    <textarea x-model="editTemplateForm.description" rows="2" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500"></textarea>
                </div>
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Prefixo Padrão</label>
                        <input type="text" x-model="editTemplateForm.prefix" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 font-mono bg-slate-950 text-slate-100 focus:border-blue-500">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Visibilidade</label>
                        <select x-model="editTemplateForm.visibility" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                            <option value="private">Privado</option>
                            <option value="shared">Compartilhado</option>
                            <option value="public" x-show="currentUser.role === 'epy_root'">Público (Root)</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Comando Executável</label>
                    <input type="text" x-model="editTemplateForm.command" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 font-mono bg-slate-950 text-slate-100 focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Argumentos (Separados por espaço)</label>
                    <input type="text" x-model="editTemplateForm.argsText" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 font-mono bg-slate-950 text-slate-100 focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Variáveis de Ambiente Padrão (JSON)</label>
                    <textarea x-model="editTemplateForm.envText" rows="3" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 font-mono bg-slate-950 text-slate-100 focus:border-blue-500"></textarea>
                </div>
            </div>
            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button @click="showEditTemplateModal = false" class="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg">Cancelar</button>
                <button @click="saveEditedTemplate()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs">Salvar Modelo</button>
            </div>
        </div>
    </div>

    <!-- Modal: Criar Novo Kit de Conhecimento -->
    <div x-show="showCreateKitModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4" @click.self="showCreateKitModal = false">
        <div class="bg-slate-900 rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-750 text-slate-100 space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                <h3 class="text-sm font-bold text-slate-100 flex items-center gap-2">
                    <i class="fa-solid fa-circle-plus text-blue-400"></i> Criar Novo Kit de Conhecimento
                </h3>
                <button type="button" @click="showCreateKitModal = false" class="text-slate-400 hover:text-slate-200"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-3 max-h-[70vh] overflow-y-auto pr-1">
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Nome do Kit</label>
                        <input type="text" x-model="createKitForm.name" placeholder="Ex: Kit Operacional Padrão" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Categoria</label>
                        <input type="text" x-model="createKitForm.category" placeholder="Ex: Operações, Compras, Geral" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Descrição</label>
                    <textarea x-model="createKitForm.description" rows="2" placeholder="Descreva os tipos de dados e diretrizes incluídos neste kit..." class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500"></textarea>
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Visibilidade</label>
                    <select x-model="createKitForm.visibility" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                        <option value="private">Privado</option>
                        <option value="shared">Compartilhado</option>
                        <option value="public" x-show="currentUser.role === 'epy_root'">Público (Root)</option>
                    </select>
                </div>

                <!-- Fontes cadastradas no Novo Kit -->
                <div class="pt-2 border-t border-slate-800 space-y-3">
                    <div class="flex items-center justify-between">
                        <div>
                            <span class="text-xs font-bold uppercase tracking-wider text-slate-300">Fontes Operacionais do Kit (<span x-text="(createKitForm.sources || []).length"></span>)</span>
                            <p class="text-[11px] text-slate-400">Nós operacionais incluídos neste pacote para orientar a IA.</p>
                        </div>
                        <button type="button" @click="addCreateKitSource()" class="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1">
                            <i class="fa-solid fa-plus text-[10px]"></i> Adicionar Fonte
                        </button>
                    </div>

                    <div class="space-y-3">
                        <template x-for="(s, sIdx) in createKitForm.sources" :key="sIdx">
                            <div class="p-3.5 rounded-xl border border-slate-750 bg-slate-950/70 space-y-2.5 relative">
                                <button type="button" @click="removeCreateKitSource(sIdx)" class="absolute top-2.5 right-2.5 text-slate-400 hover:text-rose-400 text-xs p-1" title="Remover Fonte">
                                    <i class="fa-solid fa-xmark"></i>
                                </button>
                                
                                <div class="grid grid-cols-1 md:grid-cols-3 gap-2 pr-6">
                                    <div>
                                        <label class="block text-[10px] text-slate-400 uppercase font-semibold">ID do Nó</label>
                                        <input type="text" x-model="s.id" placeholder="ex: example.procurement.messages" class="w-full text-xs font-mono border border-slate-700 rounded p-1.5 bg-slate-900 text-blue-400">
                                    </div>
                                    <div>
                                        <label class="block text-[10px] text-slate-400 uppercase font-semibold">Nome da Fonte</label>
                                        <input type="text" x-model="s.name" placeholder="ex: Equipe - Compras" class="w-full text-xs border border-slate-700 rounded p-1.5 bg-slate-900 text-slate-100">
                                    </div>
                                    <div>
                                        <label class="block text-[10px] text-slate-400 uppercase font-semibold">Propósito (Purpose)</label>
                                        <input type="text" x-model="s.purpose" placeholder="ex: procurement_tracking" class="w-full text-xs font-mono border border-slate-700 rounded p-1.5 bg-slate-900 text-slate-100">
                                    </div>
                                </div>

                                <div class="grid grid-cols-1 md:grid-cols-3 gap-2">
                                    <div>
                                        <label class="block text-[10px] text-slate-400 uppercase font-semibold">Sistema</label>
                                        <input type="text" x-model="s.system" placeholder="ex: gdrive, periskope" class="w-full text-xs border border-slate-700 rounded p-1.5 bg-slate-900 text-slate-100">
                                    </div>
                                    <div>
                                        <label class="block text-[10px] text-slate-400 uppercase font-semibold">Tipo de Recurso</label>
                                        <input type="text" x-model="s.resource_type" placeholder="ex: spreadsheet, whatsapp_group" class="w-full text-xs border border-slate-700 rounded p-1.5 bg-slate-900 text-slate-100">
                                    </div>
                                    <div>
                                        <label class="block text-[10px] text-slate-400 uppercase font-semibold">ID Nativo (Opcional)</label>
                                        <input type="text" x-model="s.native_resource_id" placeholder="ex: ID da Planilha ou JID" class="w-full text-xs font-mono border border-slate-700 rounded p-1.5 bg-slate-900 text-emerald-400">
                                    </div>
                                </div>

                                <div>
                                    <div class="flex items-center justify-between mb-1">
                                        <label class="block text-[10px] font-semibold text-slate-400 uppercase">Tags de Descoberta</label>
                                        <span class="text-[10px] text-slate-500">Pressione Enter ou vírgula</span>
                                    </div>
                                    <div class="p-1.5 rounded-lg border border-slate-700 bg-slate-900 flex flex-wrap items-center gap-1 min-h-[36px]">
                                        <template x-for="(tag, tIdx) in (s.tags || [])" :key="tIdx">
                                            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-950 border border-blue-800 text-blue-300 text-[11px] font-mono">
                                                <span x-text="tag"></span>
                                                <button type="button" @click.stop="removeTag(s, tIdx)" class="text-blue-400 hover:text-rose-400 ml-0.5"><i class="fa-solid fa-xmark text-[9px]"></i></button>
                                            </span>
                                        </template>
                                        <input type="text" placeholder="+ Tag..." @keydown.enter.prevent="addTagFromInput(s, $event)" @keydown="if ($event.key === ',') { $event.preventDefault(); addTagFromInput(s, $event); }" @blur="addTagFromInput(s, $event)" class="flex-1 min-w-[100px] text-xs bg-transparent text-slate-200 placeholder-slate-500 focus:outline-hidden py-0.5 px-1">
                                    </div>
                                    <div class="mt-1 flex flex-wrap items-center gap-1 text-[10px] text-slate-400">
                                        <span class="text-slate-500">Sugestões:</span>
                                        <template x-for="sug in getSuggestedTags(s)" :key="sug">
                                            <button type="button" @click="addSuggestedTag(s, sug)" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 font-mono text-[10px]">+ <span x-text="sug"></span></button>
                                        </template>
                                    </div>
                                </div>

                                <div>
                                    <label class="block text-[10px] text-slate-400 uppercase font-semibold">Diretriz de Consulta (Guidance)</label>
                                    <input type="text" x-model="s.guidance" placeholder="Oriente o agente sobre quando e como consultar esta fonte..." class="w-full text-xs border border-slate-700 rounded p-1.5 bg-slate-900 text-slate-100">
                                </div>
                            </div>
                        </template>

                        <template x-if="(createKitForm.sources || []).length === 0">
                            <p class="text-xs text-slate-500 italic p-3 text-center border border-dashed border-slate-800 rounded-lg">Nenhuma fonte adicionada ainda. Clique em "+ Adicionar Fonte" acima.</p>
                        </template>
                    </div>
                </div>
            </div>
            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button type="button" @click="showCreateKitModal = false" class="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg">Cancelar</button>
                <button type="button" @click="createKitSubmit()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs">Criar Kit</button>
            </div>
        </div>
    </div>

    <!-- Modal: Editar Kit de Conhecimento -->
    <div x-show="showEditKitModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4" @click.self="showEditKitModal = false">
        <div class="bg-slate-900 rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-750 text-slate-100 space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                <h3 class="text-sm font-bold text-slate-100 flex items-center gap-2">
                    <i class="fa-solid fa-book-atlas text-blue-400"></i> Editar Kit de Conhecimento
                </h3>
                <button type="button" @click="showEditKitModal = false" class="text-slate-400 hover:text-slate-200"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-3 max-h-[70vh] overflow-y-auto pr-1">
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Nome do Kit</label>
                        <input type="text" x-model="editKitForm.name" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Categoria</label>
                        <input type="text" x-model="editKitForm.category" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Descrição</label>
                    <textarea x-model="editKitForm.description" rows="2" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500"></textarea>
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Visibilidade</label>
                    <select x-model="editKitForm.visibility" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                        <option value="private">Privado</option>
                        <option value="shared">Compartilhado</option>
                        <option value="public" x-show="currentUser.role === 'epy_root'">Público (Root)</option>
                    </select>
                </div>

                <!-- Fontes cadastradas no Kit -->
                <div class="pt-2 border-t border-slate-800 space-y-3">
                    <div class="flex items-center justify-between">
                        <div>
                            <span class="text-xs font-bold uppercase tracking-wider text-slate-300">Fontes Operacionais do Kit (<span x-text="(editKitForm.sources || []).length"></span>)</span>
                            <p class="text-[11px] text-slate-400">Nós operacionais incluídos neste kit.</p>
                        </div>
                        <button type="button" @click="addEditKitSource()" class="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1">
                            <i class="fa-solid fa-plus text-[10px]"></i> Adicionar Fonte
                        </button>
                    </div>
                    <div class="space-y-3">
                        <template x-for="(s, sIdx) in editKitForm.sources" :key="sIdx">
                            <div class="p-3.5 rounded-xl border border-slate-750 bg-slate-950/70 space-y-2.5 relative">
                                <button type="button" @click="removeEditKitSource(sIdx)" class="absolute top-2.5 right-2.5 text-slate-400 hover:text-rose-400 text-xs p-1" title="Remover Fonte">
                                    <i class="fa-solid fa-xmark"></i>
                                </button>
                                
                                <div class="grid grid-cols-1 md:grid-cols-3 gap-2 pr-6">
                                    <div>
                                        <label class="block text-[10px] text-slate-400 uppercase font-semibold">ID do Nó</label>
                                        <input type="text" x-model="s.id" placeholder="ex: example.procurement.messages" class="w-full text-xs font-mono border border-slate-700 rounded p-1.5 bg-slate-900 text-blue-400">
                                    </div>
                                    <div>
                                        <label class="block text-[10px] text-slate-400 uppercase font-semibold">Nome da Fonte</label>
                                        <input type="text" x-model="s.name" placeholder="ex: Equipe - Compras" class="w-full text-xs border border-slate-700 rounded p-1.5 bg-slate-900 text-slate-100">
                                    </div>
                                    <div>
                                        <label class="block text-[10px] text-slate-400 uppercase font-semibold">Propósito (Purpose)</label>
                                        <input type="text" x-model="s.purpose" placeholder="ex: procurement_tracking" class="w-full text-xs font-mono border border-slate-700 rounded p-1.5 bg-slate-900 text-slate-100">
                                    </div>
                                </div>

                                <div class="grid grid-cols-1 md:grid-cols-3 gap-2">
                                    <div>
                                        <label class="block text-[10px] text-slate-400 uppercase font-semibold">Sistema</label>
                                        <input type="text" x-model="s.system" placeholder="ex: gdrive, periskope" class="w-full text-xs border border-slate-700 rounded p-1.5 bg-slate-900 text-slate-100">
                                    </div>
                                    <div>
                                        <label class="block text-[10px] text-slate-400 uppercase font-semibold">Tipo de Recurso</label>
                                        <input type="text" x-model="s.resource_type" placeholder="ex: spreadsheet, whatsapp_group" class="w-full text-xs border border-slate-700 rounded p-1.5 bg-slate-900 text-slate-100">
                                    </div>
                                    <div>
                                        <label class="block text-[10px] text-slate-400 uppercase font-semibold">ID Nativo (Opcional)</label>
                                        <input type="text" x-model="s.native_resource_id" placeholder="ex: ID da Planilha ou JID" class="w-full text-xs font-mono border border-slate-700 rounded p-1.5 bg-slate-900 text-emerald-400">
                                    </div>
                                </div>

                                <div>
                                    <div class="flex items-center justify-between mb-1">
                                        <label class="block text-[10px] font-semibold text-slate-400 uppercase">Tags de Descoberta</label>
                                        <span class="text-[10px] text-slate-500">Pressione Enter ou vírgula</span>
                                    </div>
                                    <div class="p-1.5 rounded-lg border border-slate-700 bg-slate-900 flex flex-wrap items-center gap-1 min-h-[36px]">
                                        <template x-for="(tag, tIdx) in (s.tags || [])" :key="tIdx">
                                            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-950 border border-blue-800 text-blue-300 text-[11px] font-mono">
                                                <span x-text="tag"></span>
                                                <button type="button" @click.stop="removeTag(s, tIdx)" class="text-blue-400 hover:text-rose-400 ml-0.5"><i class="fa-solid fa-xmark text-[9px]"></i></button>
                                            </span>
                                        </template>
                                        <input type="text" placeholder="+ Tag..." @keydown.enter.prevent="addTagFromInput(s, $event)" @keydown="if ($event.key === ',') { $event.preventDefault(); addTagFromInput(s, $event); }" @blur="addTagFromInput(s, $event)" class="flex-1 min-w-[100px] text-xs bg-transparent text-slate-200 placeholder-slate-500 focus:outline-hidden py-0.5 px-1">
                                    </div>
                                    <div class="mt-1 flex flex-wrap items-center gap-1 text-[10px] text-slate-400">
                                        <span class="text-slate-500">Sugestões:</span>
                                        <template x-for="sug in getSuggestedTags(s)" :key="sug">
                                            <button type="button" @click="addSuggestedTag(s, sug)" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 font-mono text-[10px]">+ <span x-text="sug"></span></button>
                                        </template>
                                    </div>
                                </div>

                                <div>
                                    <label class="block text-[10px] text-slate-400 uppercase font-semibold">Diretriz de Consulta (Guidance)</label>
                                    <input type="text" x-model="s.guidance" placeholder="Oriente o agente sobre quando e como consultar esta fonte..." class="w-full text-xs border border-slate-700 rounded p-1.5 bg-slate-900 text-slate-100">
                                </div>
                            </div>
                        </template>

                        <template x-if="(editKitForm.sources || []).length === 0">
                            <p class="text-xs text-slate-500 italic p-3 text-center border border-dashed border-slate-800 rounded-lg">Nenhuma fonte cadastrada neste kit.</p>
                        </template>
                    </div>
                </div>
            </div>
            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button type="button" @click="showEditKitModal = false" class="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg">Cancelar</button>
                <button type="button" @click="saveEditedKit()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs">Salvar Alterações</button>
            </div>
        </div>
    </div>

    <!-- Modal: Editar Instância -->
    <div x-show="showEditInstanceModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4" @click.self="showEditInstanceModal = false">
        <div class="bg-slate-900 rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-750 text-slate-100 space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                <h3 class="text-sm font-bold text-slate-100 flex items-center gap-2">
                    <i class="fa-solid fa-pen-to-square text-blue-400"></i> Editar Detalhes da Instância
                </h3>
                <button @click="showEditInstanceModal = false" class="text-slate-400 hover:text-slate-200"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Identificador Slug (Fixo)</label>
                    <input type="text" x-model="editInstanceForm.slug" disabled class="w-full text-xs border border-slate-800 rounded-lg p-2.5 font-mono bg-slate-950/50 text-slate-400 cursor-not-allowed">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Nome da Instância</label>
                    <input type="text" x-model="editInstanceForm.name" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Descrição Operacional</label>
                    <textarea x-model="editInstanceForm.description" rows="3" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500"></textarea>
                </div>
            </div>
            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button @click="showEditInstanceModal = false" class="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg">Cancelar</button>
                <button @click="saveEditedInstance()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs">Salvar Alterações</button>
            </div>
        </div>
    </div>

    <!-- Modal: Criar Nova Conexão Manual -->
    <div x-show="showCreateConnectionModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4" @click.self="showCreateConnectionModal = false">
        <div class="bg-slate-900 rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-750 text-slate-100 space-y-4 max-h-[90vh] overflow-y-auto">
            <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                <div class="flex items-center gap-2">
                    <div class="w-8 h-8 rounded-lg bg-blue-950/60 text-blue-400 border border-blue-800/50 flex items-center justify-center text-sm font-bold shrink-0">
                        <i class="fa-solid fa-plus"></i>
                    </div>
                    <div>
                        <h3 class="text-sm font-bold text-slate-100">Nova Conexão Manual</h3>
                        <p class="text-[11px] text-slate-400">Configure uma conexão direta escolhendo o método e parâmetros do zero.</p>
                    </div>
                </div>
                <button @click="showCreateConnectionModal = false" class="text-slate-400 hover:text-slate-200"><i class="fa-solid fa-xmark"></i></button>
            </div>

            <div class="space-y-3">
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">ID Único da Conexão *</label>
                        <input type="text" x-model="newConnectionForm.id" placeholder="ex: postgres-db" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 font-mono bg-slate-950 text-slate-100 placeholder-slate-600 focus:border-blue-500">
                        <span class="text-[10px] text-slate-500 mt-0.5 block">Identificador permanente no cofre</span>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Prefixo das Tools *</label>
                        <input type="text" x-model="newConnectionForm.prefix" placeholder="ex: db" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 font-mono bg-slate-950 text-slate-100 placeholder-slate-600 focus:border-blue-500">
                        <span class="text-[10px] text-slate-500 mt-0.5 block">Namespace: <span class="font-mono text-blue-400" x-text="(newConnectionForm.prefix || 'prefix') + '__*'"></span></span>
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Nome Amigável *</label>
                    <input type="text" x-model="newConnectionForm.name" placeholder="Ex: PostgreSQL Principal" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 placeholder-slate-600 focus:border-blue-500">
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Método de Conexão *</label>
                        <select x-model="newConnectionForm.type" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                            <option value="stdio">stdio (Executável CLI Local)</option>
                            <option value="remote_mcp">remote_mcp (Endpoint SSE)</option>
                            <option value="openapi">openapi (API REST / OpenAPI)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Visibilidade Inicial *</label>
                        <select x-model="newConnectionForm.visibility" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                            <option value="shared">Compartilhado (Equipe)</option>
                            <option value="private">Privado (Apenas Você)</option>
                            <option value="public" x-show="currentUser.role === 'epy_root'">Público (Todos - Root)</option>
                        </select>
                    </div>
                </div>

                <!-- Vincular Opcionalmente à Instância -->
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Vincular Imediatamente à Instância (Opcional)</label>
                    <select x-model="newConnectionForm.targetInstanceSlug" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                        <option value="">Apenas guardar no cofre (sem vincular)</option>
                        <template x-for="inst in instances" :key="inst.slug">
                            <option :value="inst.slug" x-text="inst.name + ' (' + inst.slug + ')'"></option>
                        </template>
                    </select>
                </div>

                <!-- Campos específicos para STDIO -->
                <template x-if="newConnectionForm.type === 'stdio'">
                    <div class="space-y-3 p-3.5 bg-slate-950/60 rounded-xl border border-slate-800">
                        <div class="flex items-center justify-between">
                            <span class="text-[11px] font-bold text-slate-300 uppercase tracking-wider"><i class="fa-solid fa-terminal text-blue-400 mr-1"></i> Configuração Stdio</span>
                            <span class="text-[10px] text-slate-500">Permitido: npx com pacote e versão exata da allowlist</span>
                        </div>
                        <div>
                            <label class="block text-xs font-medium text-slate-300 mb-1">Comando Executável *</label>
                            <input type="text" x-model="newConnectionForm.command" placeholder="Ex: npx" class="w-full text-xs border border-slate-700 rounded-lg p-2 font-mono bg-slate-900 text-slate-100 placeholder-slate-600 focus:border-blue-500">
                        </div>
                        <div>
                            <label class="block text-xs font-medium text-slate-300 mb-1">Argumentos (separados por espaço ou array JSON)</label>
                            <input type="text" x-model="newConnectionForm.argsText" placeholder="Ex: -y @modelcontextprotocol/server-postgres postgresql://..." class="w-full text-xs border border-slate-700 rounded-lg p-2 font-mono bg-slate-900 text-slate-100 placeholder-slate-600 focus:border-blue-500">
                        </div>
                        <div>
                            <label class="block text-xs font-medium text-slate-300 mb-1">Variáveis de Ambiente (JSON)</label>
                            <textarea x-model="newConnectionForm.envText" rows="2" placeholder='{"API_KEY": "..."}' class="w-full text-xs border border-slate-700 rounded-lg p-2 font-mono bg-slate-900 text-slate-100 placeholder-slate-600 focus:border-blue-500"></textarea>
                        </div>
                    </div>
                </template>

                <!-- Campos específicos para REMOTE_MCP e OPENAPI -->
                <template x-if="newConnectionForm.type === 'remote_mcp' || newConnectionForm.type === 'openapi'">
                    <div class="space-y-3 p-3.5 bg-slate-950/60 rounded-xl border border-slate-800">
                        <div class="flex items-center justify-between">
                            <span class="text-[11px] font-bold text-slate-300 uppercase tracking-wider"><i class="fa-solid fa-network-wired text-blue-400 mr-1"></i> Endpoint Remoto</span>
                        </div>
                        <div>
                            <label class="block text-xs font-medium text-slate-300 mb-1">URL do Serviço *</label>
                            <input type="text" x-model="newConnectionForm.url" placeholder="https://api.exemplo.com/mcp" class="w-full text-xs border border-slate-700 rounded-lg p-2 font-mono bg-slate-900 text-slate-100 placeholder-slate-600 focus:border-blue-500">
                        </div>
                        <div>
                            <label class="block text-xs font-medium text-slate-300 mb-1">Headers & Autenticação (JSON)</label>
                            <textarea x-model="newConnectionForm.authConfigText" rows="2" placeholder='{"Authorization": "Bearer token"}' class="w-full text-xs border border-slate-700 rounded-lg p-2 font-mono bg-slate-900 text-slate-100 placeholder-slate-600 focus:border-blue-500"></textarea>
                        </div>
                    </div>
                </template>
            </div>

            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button @click="showCreateConnectionModal = false" class="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors">Cancelar</button>
                <button @click="submitCreateConnection()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors flex items-center gap-1.5">
                    <i class="fa-solid fa-check text-[11px]"></i> Salvar Conexão
                </button>
            </div>
        </div>
    </div>

    <!-- Modal: Criar Novo Modelo de Conexão do Zero -->
    <div x-show="showCreateTemplateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4" @click.self="showCreateTemplateModal = false">
        <div class="bg-slate-900 rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-750 text-slate-100 space-y-4 max-h-[90vh] overflow-y-auto">
            <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                <div class="flex items-center gap-2">
                    <div class="w-8 h-8 rounded-lg bg-blue-950/60 text-blue-400 border border-blue-800/50 flex items-center justify-center text-sm font-bold shrink-0">
                        <i class="fa-solid fa-wand-magic-sparkles"></i>
                    </div>
                    <div>
                        <h3 class="text-sm font-bold text-slate-100">Novo Modelo de Conexão (Receita)</h3>
                        <p class="text-[11px] text-slate-400">Defina um modelo reutilizável para conectar novos serviços em 1 clique.</p>
                    </div>
                </div>
                <button @click="showCreateTemplateModal = false" class="text-slate-400 hover:text-slate-200"><i class="fa-solid fa-xmark"></i></button>
            </div>

            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Nome do Modelo *</label>
                    <input type="text" x-model="newTemplateForm.name" placeholder="Ex: PostgreSQL Database Connector" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 placeholder-slate-600 focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Descrição</label>
                    <textarea x-model="newTemplateForm.description" rows="2" placeholder="Descreva para sua equipe a finalidade deste conector..." class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 placeholder-slate-600 focus:border-blue-500"></textarea>
                </div>
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Prefixo Sugerido *</label>
                        <input type="text" x-model="newTemplateForm.prefix" placeholder="Ex: pg, github" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 font-mono bg-slate-950 text-slate-100 placeholder-slate-600 focus:border-blue-500">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Método de Conexão *</label>
                        <select x-model="newTemplateForm.type" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                            <option value="stdio">stdio (Executável CLI)</option>
                            <option value="remote_mcp">remote_mcp (Endpoint SSE)</option>
                            <option value="openapi">openapi (API REST)</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Visibilidade do Modelo *</label>
                    <select x-model="newTemplateForm.visibility" class="w-full text-xs border border-slate-700 rounded-lg p-2.5 bg-slate-950 text-slate-100 focus:border-blue-500">
                        <option value="shared">Compartilhado (Equipe)</option>
                        <option value="private">Privado (Apenas Você)</option>
                        <option value="public" x-show="currentUser.role === 'epy_root'">Público (Todos - Root)</option>
                    </select>
                </div>

                <div class="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800 space-y-3">
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Comando Padrão (para stdio)</label>
                        <input type="text" x-model="newTemplateForm.command" placeholder="Ex: npx, python, uvx" class="w-full text-xs border border-slate-700 rounded-lg p-2 font-mono bg-slate-900 text-slate-100 placeholder-slate-600 focus:border-blue-500">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Argumentos Padrão</label>
                        <input type="text" x-model="newTemplateForm.argsText" placeholder="Ex: -y @modelcontextprotocol/server-postgres" class="w-full text-xs border border-slate-700 rounded-lg p-2 font-mono bg-slate-900 text-slate-100 placeholder-slate-600 focus:border-blue-500">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Variáveis de Ambiente Padrão (JSON)</label>
                        <textarea x-model="newTemplateForm.envText" rows="2" placeholder='{"DATABASE_URL": "postgresql://..."}' class="w-full text-xs border border-slate-700 rounded-lg p-2 font-mono bg-slate-900 text-slate-100 placeholder-slate-600 focus:border-blue-500"></textarea>
                    </div>
                </div>
            </div>

            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button @click="showCreateTemplateModal = false" class="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors">Cancelar</button>
                <button @click="submitCreateTemplate()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors flex items-center gap-1.5">
                    <i class="fa-solid fa-wand-magic-sparkles text-[11px]"></i> Salvar Modelo
                </button>
            </div>
        </div>
    </div>
    <!-- Modal: segredo emitido uma única vez -->
    <div x-show="showIssuedTokenModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4" @click.self="closeIssuedTokenModal()">
        <div class="bg-slate-900 rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-amber-700/50 text-slate-100 space-y-4">
            <div>
                <h3 class="text-sm font-bold text-amber-300">Salve este token agora</h3>
                <p class="text-xs text-slate-400 mt-1">O valor não será armazenado em texto simples nem exibido novamente.</p>
            </div>
            <code class="block break-all rounded-lg border border-slate-700 bg-slate-950 p-3 text-xs text-emerald-400" x-text="issuedToken"></code>
            <div class="flex justify-end gap-2">
                <button @click="copyText(issuedToken, 'Token copiado!')" class="px-3 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-xs font-semibold">Copiar token</button>
                <button @click="closeIssuedTokenModal()" class="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-xs font-semibold">Já salvei</button>
            </div>
        </div>
    </div>

    <script>
        function centralApp() {
            return {
                showCreateConnectionModal: false,
                newConnectionForm: { id: '', name: '', prefix: '', type: 'stdio', command: '', argsText: '', envText: '{}', url: '', authConfigText: '{}', visibility: 'shared', targetInstanceSlug: '' },
                showCreateTemplateModal: false,
                newTemplateForm: { name: '', description: '', prefix: '', type: 'stdio', command: '', argsText: '', envText: '{}', authConfigText: '{}', visibility: 'shared' },
                activeTab: 'instances',
                studioTab: 'connections',
                vaultSubTab: 'active',
                govSubTab: 'users',
                visibilityFilter: 'all',
                loading: false,
                adminKey: '',
                sessionToken: '',
                showAuthModal: false,
                showUserModal: false,
                showCreateUserModal: false,
                showCreateInstanceModal: false,
                showIssuedTokenModal: false,
                issuedToken: '',
                showTemplateModal: false,
                showSaveAsTemplateModal: false,
                showSaveAsKitModal: false,
                showCreateKitModal: false,
                createKitForm: { name: '', category: 'Operações', description: '', visibility: 'shared', sources: [] },
                showConfirmModal: false,
                showInstantiateModal: false,
                showEditConnectionModal: false,
                editConnectionForm: { id: '', name: '', prefix: '', type: 'stdio', command: '', argsText: '', envText: '{}', url: '', authConfigText: '{}', visibility: 'shared' },
                showEditTemplateModal: false,
                editTemplateForm: { id: '', name: '', description: '', prefix: '', type: 'stdio', command: '', argsText: '', envText: '{}', visibility: 'shared' },
                showEditKitModal: false,
                editKitForm: { id: '', name: '', category: 'Geral', description: '', visibility: 'shared', sources: [] },
                showEditInstanceModal: false,
                editInstanceForm: { slug: '', name: '', description: '' },
                showShareModal: false,
                shareTargetType: 'connection',
                shareTargetId: '',
                shareTargetName: '',
                shareSelectedUserIds: [],
                shareSearchQuery: '',
                authTab: 'login',
                useAdminKeyLogin: false,
                loginForm: { username: '', password: '' },
                registerForm: { username: '', display_name: '', password: '', invite_code: '' },
                pendingUsers: [],
                invitesList: [],
                inviteHours: '24',
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
                presentIssuedToken(token) {
                    if (!token) return;
                    this.issuedToken = token;
                    this.showIssuedTokenModal = true;
                },
                closeIssuedTokenModal() {
                    this.showIssuedTokenModal = false;
                    this.issuedToken = '';
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
                    return this.instanceTools.filter(t => 
                        (t.namespaced_name || t.name || '').toLowerCase().includes(q) || 
                        (t.title || '').toLowerCase().includes(q) || 
                        (t.description || '').toLowerCase().includes(q) ||
                        (t.connection_id || '').toLowerCase().includes(q)
                    );
                },
                get availableConnectionsToAttach() {
                    if (!this.currentInstanceDetail) return this.connections;
                    const attachedIds = (this.currentInstanceDetail.connections || []).map(c => c.id);
                    return this.connections.filter(c => !attachedIds.includes(c.id));
                },
                get filteredShareUsers() {
                    if (!this.shareSearchQuery) return this.usersList;
                    const q = this.shareSearchQuery.toLowerCase();
                    return this.usersList.filter(u => 
                        (u.username || '').toLowerCase().includes(q) || 
                        (u.display_name || '').toLowerCase().includes(q)
                    );
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
                        this.showAuthModal = false;
                        this.refreshAll();
                    }
                },

                async initApp() {
                    const params = new URLSearchParams(window.location.search);
                    const qInvite = params.get('invite');
                    if (qInvite) {
                        this.authTab = 'register';
                        this.registerForm.invite_code = qInvite.trim();
                        this.showAuthModal = true;
                    }
                    if (!this.adminKey && !this.sessionToken && !qInvite) {
                        this.showAuthModal = true;
                        return;
                    }
                    await this.fetchMe();
                    await this.refreshAll();
                    if (this.instances.length > 0 && !this.selectedInstanceSlug) {
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
                        const tasks = [
                            this.fetchOverview(),
                            this.fetchInstances(),
                            this.fetchConnections(),
                            this.fetchTemplates(),
                            this.fetchDataSourceKits(),
                            this.fetchUsers(),
                            this.fetchRecentLogs()
                        ];
                        if (this.currentUser && this.currentUser.role === 'epy_root') {
                            tasks.push(this.fetchInvites());
                            tasks.push(this.fetchPendingUsers());
                        }
                        await Promise.all(tasks);
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
                            this.instanceTools = Array.isArray(data) ? data : (data.tools || []);
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

                async toggleInstanceTool(slug, tool) {
                    try {
                        const toolIdentifier = tool.id || tool.namespaced_name || tool.name;
                        const targetEnabled = !tool.is_enabled;
                        const res = await this.apiFetch(`/api/v1/instances/${slug}/tools/${encodeURIComponent(toolIdentifier)}/toggle`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ is_enabled: targetEnabled })
                        });
                        if (res && res.ok) {
                            const data = await res.json();
                            tool.is_enabled = data.is_enabled;
                            this.showToast(`Ferramenta ${tool.namespaced_name || tool.name || toolIdentifier} ${data.is_enabled ? 'ativada' : 'desativada'}.`, 'info');
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
                            if (newVis === 'shared') {
                                this.openShareModal(this.currentInstanceDetail || inst, 'instance');
                            }
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
                            if (newVis === 'shared' && c) {
                                this.openShareModal(c, 'connection');
                            }
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Falha ao alterar visibilidade.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Erro na requisição.', 'error');
                    }
                },

                openShareModal(item, type) {
                    this.shareTargetType = type;
                    this.shareTargetId = (type === 'connection' ? item.id : item.slug);
                    this.shareTargetName = item.name;
                    this.shareSelectedUserIds = [...(item.shared_user_ids || [])];
                    this.shareSearchQuery = '';
                    this.showShareModal = true;
                },

                async saveShares() {
                    try {
                        const url = this.shareTargetType === 'connection' 
                            ? `/api/v1/connections/${this.shareTargetId}/shares`
                            : `/api/v1/instances/${this.shareTargetId}/shares`;
                        const res = await this.apiFetch(url, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ user_ids: this.shareSelectedUserIds })
                        });
                        if (res && res.ok) {
                            const data = await res.json();
                            if (this.shareTargetType === 'connection') {
                                const c = this.connections.find(i => i.id === this.shareTargetId);
                                if (c) c.shared_user_ids = data.shared_user_ids;
                            } else {
                                if (this.currentInstanceDetail && this.currentInstanceDetail.slug === this.shareTargetId) {
                                    this.currentInstanceDetail.shared_user_ids = data.shared_user_ids;
                                }
                                const inst = this.instances.find(i => i.slug === this.shareTargetId);
                                if (inst) inst.shared_user_ids = data.shared_user_ids;
                            }
                            this.showShareModal = false;
                            this.showToast('Compartilhamento de acesso salvo com sucesso!', 'success');
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao salvar compartilhamento.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Erro na requisição de compartilhamento.', 'error');
                    }
                },

                async fetchPendingUsers() {
                    if (this.currentUser.role !== 'epy_root') return;
                    try {
                        const res = await this.apiFetch('/api/v1/admin/pending-users');
                        if (res && res.ok) {
                            this.pendingUsers = await res.json();
                        }
                    } catch (e) {}
                },

                async fetchInvites() {
                    if (this.currentUser.role !== 'epy_root') return;
                    try {
                        const res = await this.apiFetch('/api/v1/admin/invites');
                        if (res && res.ok) {
                            this.invitesList = await res.json();
                        }
                    } catch (e) {}
                },

                async generateInvite() {
                    try {
                        const res = await this.apiFetch('/api/v1/admin/invites', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ expires_hours: parseInt(this.inviteHours) || 24, role: 'standard' })
                        });
                        if (res && res.ok) {
                            const data = await res.json();
                            this.showToast('Novo convite gerado com sucesso!', 'success');
                            await this.fetchInvites();
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao gerar convite.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Falha na comunicação.', 'error');
                    }
                },

                async deleteInvite(code) {
                    if (!confirm('Deseja realmente revogar este convite?')) return;
                    try {
                        const res = await this.apiFetch(`/api/v1/admin/invites/${code}`, { method: 'DELETE' });
                        if (res && res.ok) {
                            this.showToast('Convite revogado com sucesso.', 'info');
                            await this.fetchInvites();
                        }
                    } catch (e) {
                        this.showToast('Erro ao revogar convite.', 'error');
                    }
                },

                async approveUser(userId) {
                    try {
                        const res = await this.apiFetch(`/api/v1/admin/pending-users/${userId}/approve`, { method: 'POST' });
                        if (res && res.ok) {
                            this.showToast('Usuário aprovado com sucesso!', 'success');
                            await Promise.all([this.fetchPendingUsers(), this.fetchUsers()]);
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao aprovar usuário.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Falha ao aprovar usuário.', 'error');
                    }
                },

                async rejectUser(userId) {
                    if (!confirm('Deseja realmente rejeitar esta solicitação?')) return;
                    try {
                        const res = await this.apiFetch(`/api/v1/admin/pending-users/${userId}/reject`, { method: 'POST' });
                        if (res && res.ok) {
                            this.showToast('Solicitação de usuário rejeitada.', 'info');
                            await this.fetchPendingUsers();
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao rejeitar usuário.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Falha ao rejeitar usuário.', 'error');
                    }
                },

                async submitLogin() {
                    if (!this.loginForm.username) {
                        this.showToast('Informe o nome de usuário.', 'error');
                        return;
                    }
                    try {
                        const res = await fetch('/api/v1/auth/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(this.loginForm)
                        });
                        if (res && res.ok) {
                            const data = await res.json();
                            this.sessionToken = data.token;
                            this.showAuthModal = false;
                            this.showToast(`Bem-vindo, ${data.user.display_name || data.user.username}!`, 'success');
                            await this.fetchMe();
                            await this.refreshAll();
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Falha ao autenticar.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Erro de comunicação.', 'error');
                    }
                },

                async submitRegister() {
                    if (!this.registerForm.username || !this.registerForm.password) {
                        this.showToast('Preencha o usuário e a senha.', 'error');
                        return;
                    }
                    try {
                        const res = await fetch('/api/v1/auth/register', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(this.registerForm)
                        });
                        const data = await res.json();
                        if (res && res.ok) {
                            if (data.status === 'approved' && data.token) {
                                this.sessionToken = data.token;
                                this.showAuthModal = false;
                                this.showToast('Conta ativada com sucesso pelo convite!', 'success');
                                await this.fetchMe();
                                await this.refreshAll();
                            } else {
                                this.showToast(data.message || 'Cadastro realizado! Aguardando aprovação.', 'info');
                                this.authTab = 'login';
                            }
                            this.registerForm = { username: '', display_name: '', password: '', invite_code: '' };
                        } else {
                            this.showToast(data.detail || 'Erro ao realizar cadastro.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Erro ao enviar solicitação.', 'error');
                    }
                },

                async logout() {
                    try {
                        await this.apiFetch('/api/v1/auth/logout', { method: 'POST' });
                    } catch (e) {}
                    this.sessionToken = '';
                    this.adminKey = '';
                    this.currentUser = { username: '', role: 'standard', display_name: '', is_master_admin: false };
                    this.showAuthModal = true;
                    this.authTab = 'login';
                    this.showToast('Sessão encerrada.', 'info');
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
                    if (!this.sourcesMapData) {
                        this.sourcesMapData = { organization: (this.currentInstanceDetail ? this.currentInstanceDetail.name : 'Example Organization'), sources: [] };
                    }
                    if (!Array.isArray(this.sourcesMapData.sources)) {
                        this.sourcesMapData.sources = [];
                    }
                    const ts = Date.now();
                    const newSource = {
                        id: `source.node_${ts}`,
                        name: 'Nova Fonte Operacional',
                        purpose: 'general_operations',
                        tags: ['operations', 'official'],
                        system: 'gdrive',
                        authority: 'official',
                        status: 'active',
                        resource_type: 'spreadsheet',
                        native_resource_id: '',
                        content_types: ['documentos'],
                        primary_tools: [],
                        guidance: 'Consulte esta fonte para obter informações sobre...'
                    };
                    this.sourcesMapData = {
                        ...this.sourcesMapData,
                        sources: [...this.sourcesMapData.sources, newSource]
                    };
                    this.showToast('Nova fonte adicionada ao mapa! Edite os detalhes e salve.', 'info');
                },

                removeSourceItem(index) {
                    if (!this.sourcesMapData || !this.sourcesMapData.sources) return;
                    this.sourcesMapData = {
                        ...this.sourcesMapData,
                        sources: this.sourcesMapData.sources.filter((_, i) => i !== index)
                    };
                },

                addTagFromInput(source, event) {
                    const raw = (event.target.value || '').trim();
                    if (!raw) return;
                    const parts = raw.split(/[ ,;]+/).map(p => p.toLowerCase().trim()).filter(Boolean);
                    if (!source.tags) source.tags = [];
                    for (const p of parts) {
                        const clean = p.replace(/[^a-z0-9_.-]/g, '');
                        if (clean && !source.tags.includes(clean)) {
                            source.tags.push(clean);
                        }
                    }
                    event.target.value = '';
                },

                removeTag(source, index) {
                    if (source && source.tags && source.tags.length > index) {
                        source.tags.splice(index, 1);
                    }
                },

                addSuggestedTag(source, tag) {
                    if (!source) return;
                    if (!source.tags) source.tags = [];
                    const clean = (tag || '').toLowerCase().trim();
                    if (clean && !source.tags.includes(clean)) {
                        source.tags.push(clean);
                    }
                },

                getSuggestedTags(source) {
                    if (!source) return [];
                    const existing = new Set((source.tags || []).map(t => (t || '').toLowerCase()));
                    const suggestions = [];
                    if (source.system) {
                        const sys = source.system.toLowerCase().trim();
                        if (sys && !existing.has(sys)) suggestions.push(sys);
                    }
                    if (source.resource_type) {
                        const rt = source.resource_type.toLowerCase().trim();
                        if (rt && !existing.has(rt)) suggestions.push(rt);
                    }
                    if (source.purpose) {
                        const purpParts = source.purpose.toLowerCase().split(/[ _-]+/).filter(Boolean);
                        for (const pp of purpParts) {
                            if (!existing.has(pp) && pp.length > 2) suggestions.push(pp);
                        }
                    }
                    const common = ['official', 'compras', 'operacoes', 'whatsapp', 'planilha', 'ssot', 'vault'];
                    for (const c of common) {
                        if (!existing.has(c) && !suggestions.includes(c)) {
                            suggestions.push(c);
                        }
                    }
                    return suggestions.slice(0, 6);
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
                            this.presentIssuedToken(data.token);
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
                                target_instance_slug: this.templateTargetInstanceSlug || 'demo-suite'
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

                openCreateConnectionModal(targetSlug = '') {
                    this.newConnectionForm = {
                        id: '',
                        name: '',
                        prefix: '',
                        type: 'stdio',
                        command: '',
                        argsText: '',
                        envText: '{}',
                        url: '',
                        authConfigText: '{}',
                        visibility: 'shared',
                        targetInstanceSlug: targetSlug || (this.selectedInstanceSlug || '')
                    };
                    this.showCreateConnectionModal = true;
                },

                async submitCreateConnection() {
                    if (!this.newConnectionForm.id || !this.newConnectionForm.name || !this.newConnectionForm.prefix) {
                        this.showToast('Preencha os campos obrigatórios (ID, Nome e Prefixo).', 'error');
                        return;
                    }
                    const cleanId = this.newConnectionForm.id.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '-');
                    if (!cleanId) {
                        this.showToast('ID da conexão inválido.', 'error');
                        return;
                    }

                    try {
                        let parsedArgs = [];
                        const trimmedArgs = (this.newConnectionForm.argsText || '').trim();
                        if (trimmedArgs.startsWith('[')) {
                            parsedArgs = JSON.parse(trimmedArgs);
                        } else if (trimmedArgs) {
                            parsedArgs = trimmedArgs.split(/\\s+/);
                        }

                        let parsedEnv = {};
                        if ((this.newConnectionForm.envText || '').trim()) {
                            parsedEnv = JSON.parse(this.newConnectionForm.envText);
                        }

                        let parsedAuth = {};
                        if ((this.newConnectionForm.authConfigText || '').trim()) {
                            parsedAuth = JSON.parse(this.newConnectionForm.authConfigText);
                        }

                        const payload = {
                            id: cleanId,
                            name: this.newConnectionForm.name.trim(),
                            prefix: this.newConnectionForm.prefix.trim().toLowerCase().replace(/[^a-z0-9_]/g, '_'),
                            type: this.newConnectionForm.type,
                            command: this.newConnectionForm.command ? this.newConnectionForm.command.trim() : null,
                            args: parsedArgs,
                            env: parsedEnv,
                            url: this.newConnectionForm.url ? this.newConnectionForm.url.trim() : null,
                            auth_config: parsedAuth,
                            visibility: this.newConnectionForm.visibility
                        };

                        const res = await this.apiFetch('/api/v1/connections', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });

                        if (res && res.ok) {
                            const data = await res.json();
                            const connId = data.connection_id || cleanId;
                            
                            if (this.newConnectionForm.targetInstanceSlug) {
                                try {
                                    await this.apiFetch(`/api/v1/instances/${this.newConnectionForm.targetInstanceSlug}/connections`, {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({ connection_id: connId })
                                    });
                                } catch (attachErr) {
                                    console.error('Falha ao vincular à instância:', attachErr);
                                }
                            }

                            this.showCreateConnectionModal = false;
                            this.showToast(`Conexão "${payload.name}" criada com sucesso!`, 'success');
                            await this.refreshAll();
                            if (this.newConnectionForm.targetInstanceSlug) {
                                await this.selectInstance(this.newConnectionForm.targetInstanceSlug);
                            }
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao criar conexão.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Erro de sintaxe JSON nos parâmetros: ' + e.message, 'error');
                    }
                },

                openCreateTemplateModal() {
                    this.newTemplateForm = {
                        name: '',
                        description: '',
                        prefix: '',
                        type: 'stdio',
                        command: '',
                        argsText: '',
                        envText: '{}',
                        authConfigText: '{}',
                        visibility: 'shared'
                    };
                    this.showCreateTemplateModal = true;
                },

                async submitCreateTemplate() {
                    if (!this.newTemplateForm.name || !this.newTemplateForm.prefix) {
                        this.showToast('Preencha os campos obrigatórios (Nome e Prefixo).', 'error');
                        return;
                    }

                    try {
                        let parsedArgs = [];
                        const trimmedArgs = (this.newTemplateForm.argsText || '').trim();
                        if (trimmedArgs.startsWith('[')) {
                            parsedArgs = JSON.parse(trimmedArgs);
                        } else if (trimmedArgs) {
                            parsedArgs = trimmedArgs.split(/\\s+/);
                        }

                        let parsedEnv = {};
                        if ((this.newTemplateForm.envText || '').trim()) {
                            parsedEnv = JSON.parse(this.newTemplateForm.envText);
                        }

                        let parsedAuth = {};
                        if ((this.newTemplateForm.authConfigText || '').trim()) {
                            parsedAuth = JSON.parse(this.newTemplateForm.authConfigText);
                        }

                        const payload = {
                            name: this.newTemplateForm.name.trim(),
                            description: (this.newTemplateForm.description || '').trim(),
                            prefix: this.newTemplateForm.prefix.trim().toLowerCase().replace(/[^a-z0-9_]/g, '_'),
                            type: this.newTemplateForm.type,
                            command: this.newTemplateForm.command ? this.newTemplateForm.command.trim() : null,
                            args: parsedArgs,
                            env: parsedEnv,
                            auth_config: parsedAuth,
                            visibility: this.newTemplateForm.visibility
                        };

                        const res = await this.apiFetch('/api/v1/connection-templates', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });

                        if (res && res.ok) {
                            this.showCreateTemplateModal = false;
                            this.showToast(`Modelo "${payload.name}" criado com sucesso!`, 'success');
                            await this.fetchTemplates();
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao criar modelo.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Erro de sintaxe JSON nos parâmetros: ' + e.message, 'error');
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
                            const data = await res.json();
                            this.presentIssuedToken(data.token);
                            this.showToast('Novo token gerado com sucesso!', 'success');
                            await this.selectInstance(this.currentInstanceDetail.slug);
                        }
                    } catch (e) {
                        this.showToast('Erro ao gerar token.', 'error');
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
                    const target = prompt('Informe o slug da instância de destino (ex: demo-suite):', 'demo-suite');
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

                // --- Edição e Exclusão Segura de Recursos ---

                openEditConnectionModal(c) {
                    this.editConnectionForm = {
                        id: c.id,
                        name: c.name || '',
                        prefix: c.prefix || c.id,
                        type: c.type || 'stdio',
                        command: c.command || '',
                        argsText: Array.isArray(c.args) ? c.args.join(' ') : (c.args || ''),
                        envText: c.env && Object.keys(c.env).length > 0 ? JSON.stringify(c.env, null, 2) : '{}',
                        url: c.url || '',
                        authConfigText: c.auth_config && Object.keys(c.auth_config).length > 0 ? JSON.stringify(c.auth_config, null, 2) : '{}',
                        visibility: c.visibility || 'shared'
                    };
                    this.showEditConnectionModal = true;
                },

                async saveEditedConnection() {
                    try {
                        let parsedArgs = [];
                        const trimmedArgs = (this.editConnectionForm.argsText || '').trim();
                        if (trimmedArgs.startsWith('[')) {
                            parsedArgs = JSON.parse(trimmedArgs);
                        } else if (trimmedArgs) {
                            parsedArgs = trimmedArgs.split(/\\s+/);
                        }
                        let parsedEnv = {};
                        if ((this.editConnectionForm.envText || '').trim()) {
                            parsedEnv = JSON.parse(this.editConnectionForm.envText);
                        }
                        let parsedAuth = {};
                        if ((this.editConnectionForm.authConfigText || '').trim()) {
                            parsedAuth = JSON.parse(this.editConnectionForm.authConfigText);
                        }
                        const payload = {
                            name: this.editConnectionForm.name,
                            prefix: this.editConnectionForm.prefix,
                            type: this.editConnectionForm.type,
                            command: this.editConnectionForm.command || null,
                            args: parsedArgs,
                            env: parsedEnv,
                            url: this.editConnectionForm.url || null,
                            auth_config: parsedAuth,
                            visibility: this.editConnectionForm.visibility
                        };
                        const res = await this.apiFetch(`/api/v1/connections/${this.editConnectionForm.id}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });
                        if (res && res.ok) {
                            this.showEditConnectionModal = false;
                            this.showToast('Conexão atualizada com sucesso!', 'success');
                            await this.refreshAll();
                            if (this.selectedInstanceSlug) await this.selectInstance(this.selectedInstanceSlug);
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao atualizar conexão.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Erro de sintaxe JSON nos parâmetros: ' + e.message, 'error');
                    }
                },

                openEditTemplateModal(t) {
                    this.editTemplateForm = {
                        id: t.id,
                        name: t.name || '',
                        description: t.description || '',
                        prefix: t.prefix || '',
                        type: t.type || 'stdio',
                        command: t.command || '',
                        argsText: Array.isArray(t.args) ? t.args.join(' ') : (t.args || ''),
                        envText: t.env && Object.keys(t.env).length > 0 ? JSON.stringify(t.env, null, 2) : '{}',
                        visibility: t.visibility || 'shared'
                    };
                    this.showEditTemplateModal = true;
                },

                async saveEditedTemplate() {
                    try {
                        let parsedArgs = [];
                        const trimmedArgs = (this.editTemplateForm.argsText || '').trim();
                        if (trimmedArgs.startsWith('[')) {
                            parsedArgs = JSON.parse(trimmedArgs);
                        } else if (trimmedArgs) {
                            parsedArgs = trimmedArgs.split(/\\s+/);
                        }
                        let parsedEnv = {};
                        if ((this.editTemplateForm.envText || '').trim()) {
                            parsedEnv = JSON.parse(this.editTemplateForm.envText);
                        }
                        const payload = {
                            name: this.editTemplateForm.name,
                            description: this.editTemplateForm.description,
                            prefix: this.editTemplateForm.prefix,
                            type: this.editTemplateForm.type,
                            command: this.editTemplateForm.command || null,
                            args: parsedArgs,
                            env: parsedEnv,
                            visibility: this.editTemplateForm.visibility
                        };
                        const res = await this.apiFetch(`/api/v1/connection-templates/${this.editTemplateForm.id}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });
                        if (res && res.ok) {
                            this.showEditTemplateModal = false;
                            this.showToast('Modelo atualizado com sucesso!', 'success');
                            await this.fetchTemplates();
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao atualizar modelo.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Erro de sintaxe JSON nos parâmetros: ' + e.message, 'error');
                    }
                },

                confirmDeleteTemplate(t) {
                    this.confirmTitle = `Excluir Modelo "${t.name}"`;
                    this.confirmMessage = 'Tem certeza que deseja excluir esta receita de modelo? Conexões já instanciadas continuarão funcionando.';
                    this.pendingConfirmAction = async () => {
                        const res = await this.apiFetch(`/api/v1/connection-templates/${t.id}`, { method: 'DELETE' });
                        if (res && res.ok) {
                            this.showToast('Modelo excluído com sucesso.', 'success');
                            await this.fetchTemplates();
                        } else {
                            this.showToast('Erro ao excluir modelo.', 'error');
                        }
                    };
                    this.showConfirmModal = true;
                },

                openCreateKitModal() {
                    this.createKitForm = {
                        name: '',
                        category: 'Operações',
                        description: '',
                        visibility: 'shared',
                        sources: []
                    };
                    this.showCreateKitModal = true;
                },

                addCreateKitSource() {
                    if (!this.createKitForm.sources) this.createKitForm.sources = [];
                    const ts = Date.now();
                    this.createKitForm.sources = [
                        ...this.createKitForm.sources,
                        {
                            id: `kit.node_${ts}`,
                            name: 'Nova Fonte do Kit',
                            purpose: 'general_operations',
                            tags: ['operations'],
                            system: 'gdrive',
                            authority: 'official',
                            status: 'active',
                            resource_type: 'spreadsheet',
                            native_resource_id: '',
                            guidance: 'Diretriz de consulta desta fonte...'
                        }
                    ];
                },

                removeCreateKitSource(index) {
                    if (!this.createKitForm || !this.createKitForm.sources) return;
                    this.createKitForm.sources = this.createKitForm.sources.filter((_, i) => i !== index);
                },

                async createKitSubmit() {
                    if (!this.createKitForm.name.trim()) {
                        this.showToast('Informe o nome do Kit de Conhecimento.', 'error');
                        return;
                    }
                    try {
                        const res = await this.apiFetch('/api/v1/data-source-kits', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(this.createKitForm)
                        });
                        if (res && res.ok) {
                            this.showCreateKitModal = false;
                            this.showToast('Kit de Conhecimento criado com sucesso!', 'success');
                            await this.fetchDataSourceKits();
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao criar kit.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Erro ao criar kit: ' + e.message, 'error');
                    }
                },

                openEditKitModal(k) {
                    this.editKitForm = {
                        id: k.id,
                        name: k.name || '',
                        category: k.category || 'Geral',
                        description: k.description || '',
                        visibility: k.visibility || 'shared',
                        sources: JSON.parse(JSON.stringify(k.sources || []))
                    };
                    this.showEditKitModal = true;
                },

                addEditKitSource() {
                    if (!this.editKitForm.sources) this.editKitForm.sources = [];
                    const ts = Date.now();
                    this.editKitForm.sources = [
                        ...this.editKitForm.sources,
                        {
                            id: `kit.node_${ts}`,
                            name: 'Nova Fonte do Kit',
                            purpose: 'general_operations',
                            tags: ['operations'],
                            system: 'gdrive',
                            authority: 'official',
                            status: 'active',
                            resource_type: 'spreadsheet',
                            native_resource_id: '',
                            guidance: 'Diretriz de consulta desta fonte...'
                        }
                    ];
                },

                removeEditKitSource(index) {
                    if (!this.editKitForm || !this.editKitForm.sources) return;
                    this.editKitForm.sources = this.editKitForm.sources.filter((_, i) => i !== index);
                },

                async saveEditedKit() {
                    try {
                        const payload = {
                            name: this.editKitForm.name,
                            category: this.editKitForm.category,
                            description: this.editKitForm.description,
                            visibility: this.editKitForm.visibility,
                            sources: this.editKitForm.sources
                        };
                        const res = await this.apiFetch(`/api/v1/data-source-kits/${this.editKitForm.id}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });
                        if (res && res.ok) {
                            this.showEditKitModal = false;
                            this.showToast('Kit de Conhecimento atualizado com sucesso!', 'success');
                            await this.fetchDataSourceKits();
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao atualizar kit.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Erro ao salvar kit: ' + e.message, 'error');
                    }
                },

                confirmDeleteKit(k) {
                    this.confirmTitle = `Excluir Kit "${k.name}"`;
                    this.confirmMessage = 'Tem certeza que deseja excluir este kit de conhecimento? Instâncias que já o utilizaram não serão afetadas.';
                    this.pendingConfirmAction = async () => {
                        const res = await this.apiFetch(`/api/v1/data-source-kits/${k.id}`, { method: 'DELETE' });
                        if (res && res.ok) {
                            this.showToast('Kit excluído com sucesso.', 'success');
                            await this.fetchDataSourceKits();
                        } else {
                            this.showToast('Erro ao excluir kit.', 'error');
                        }
                    };
                    this.showConfirmModal = true;
                },

                openEditInstanceModal(inst) {
                    this.editInstanceForm = {
                        slug: inst.slug,
                        name: inst.name || '',
                        description: inst.description || ''
                    };
                    this.showEditInstanceModal = true;
                },

                async saveEditedInstance() {
                    try {
                        const payload = {
                            name: this.editInstanceForm.name,
                            description: this.editInstanceForm.description
                        };
                        const res = await this.apiFetch(`/api/v1/instances/${this.editInstanceForm.slug}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });
                        if (res && res.ok) {
                            this.showEditInstanceModal = false;
                            this.showToast('Instância atualizada com sucesso!', 'success');
                            if (this.currentInstanceDetail && this.currentInstanceDetail.slug === this.editInstanceForm.slug) {
                                this.currentInstanceDetail.name = this.editInstanceForm.name;
                                this.currentInstanceDetail.description = this.editInstanceForm.description;
                            }
                            await this.fetchInstances();
                        } else {
                            const err = await res.json();
                            this.showToast(err.detail || 'Erro ao atualizar instância.', 'error');
                        }
                    } catch (e) {
                        this.showToast('Erro ao salvar instância: ' + e.message, 'error');
                    }
                },

                getEndpointUrl(slug) {
                    const loc = window.location;
                    const proto = loc.protocol;
                    const host = loc.host;
                    return `${proto}//${host}/mcp/${slug || 'default'}/sse`;
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
