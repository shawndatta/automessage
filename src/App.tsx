import { useCallback, useMemo, useState } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  Position,
  addEdge,
  useEdgesState,
  useNodesState,
  type Connection,
  type NodeProps,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import {
  Activity,
  ArrowLeft,
  ArrowUpRight,
  AtSign,
  Bell,
  Bot,
  Check,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  Clock3,
  ContactRound,
  Copy,
  Database,
  FileText,
  GitBranch,
  Hash,
  Inbox,
  Instagram,
  LayoutDashboard,
  Menu,
  MessageCircle,
  MessageSquareText,
  MoreHorizontal,
  PanelLeftClose,
  Play,
  Plus,
  Radio,
  Search,
  Send,
  Settings,
  Sparkles,
  Tag,
  Telegram,
  UserRound,
  Users,
  X,
  Zap,
} from 'lucide-react'
import './index.css'

type View = 'overview' | 'flows' | 'editor' | 'inbox' | 'contacts' | 'knowledge'

const navItems = [
  { id: 'overview' as View, label: 'Overview', icon: LayoutDashboard },
  { id: 'flows' as View, label: 'Automations', icon: GitBranch },
  { id: 'inbox' as View, label: 'Inbox', icon: Inbox, count: 3 },
  { id: 'contacts' as View, label: 'Contacts', icon: Users },
  { id: 'knowledge' as View, label: 'Knowledge', icon: Database },
]

const avatars = {
  maya: 'https://i.pravatar.cc/100?img=47',
  daniel: 'https://i.pravatar.cc/100?img=12',
  elena: 'https://i.pravatar.cc/100?img=32',
  jordan: 'https://i.pravatar.cc/100?img=68',
  priya: 'https://i.pravatar.cc/100?img=49',
}

function Logo() {
  return (
    <div className="brand">
      <div className="brand-mark"><MessageCircle size={19} fill="currentColor" /></div>
      <span>AutoMessage</span>
    </div>
  )
}

function Sidebar({ view, setView, open, setOpen }: { view: View; setView: (v: View) => void; open: boolean; setOpen: (v: boolean) => void }) {
  return (
    <>
      {open && <div className="mobile-overlay" onClick={() => setOpen(false)} />}
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <div className="sidebar-top">
          <Logo />
          <button className="icon-btn collapse" onClick={() => setOpen(false)}><PanelLeftClose size={18} /></button>
        </div>
        <div className="workspace-switcher">
          <div className="workspace-avatar">N</div>
          <div><strong>Northstar Studio</strong><span>Pro workspace</span></div>
          <ChevronDown size={15} />
        </div>
        <nav>
          {navItems.map(({ id, label, icon: Icon, count }) => (
            <button key={id} className={`nav-item ${view === id || (id === 'flows' && view === 'editor') ? 'active' : ''}`} onClick={() => { setView(id); setOpen(false) }}>
              <Icon size={18} />
              <span>{label}</span>
              {count && <em>{count}</em>}
            </button>
          ))}
        </nav>
        <div className="sidebar-section">
          <p>CHANNELS</p>
          <button className="channel-row"><span className="channel-icon telegram"><Telegram size={15} fill="currentColor" /></span>Telegram<span className="status-dot online" /></button>
          <button className="channel-row"><span className="channel-icon instagram"><Instagram size={15} /></span>Instagram<span className="status-dot pending" /></button>
          <button className="add-channel"><Plus size={15} /> Connect channel</button>
        </div>
        <div className="sidebar-bottom">
          <button className="nav-item"><CircleHelp size={18} /><span>Help & docs</span></button>
          <button className="nav-item"><Settings size={18} /><span>Settings</span></button>
          <div className="profile-row">
            <img src={avatars.jordan} alt="" />
            <div><strong>Jordan Lee</strong><span>jordan@northstar.co</span></div>
            <MoreHorizontal size={17} />
          </div>
        </div>
      </aside>
    </>
  )
}

function Header({ title, eyebrow, onMenu, action }: { title: string; eyebrow?: string; onMenu: () => void; action?: React.ReactNode }) {
  return (
    <header className="topbar">
      <button className="icon-btn mobile-menu" onClick={onMenu}><Menu size={20} /></button>
      <div className="page-title">{eyebrow && <span>{eyebrow}</span>}<h1>{title}</h1></div>
      <div className="top-actions">
        {action}
        <button className="icon-btn notification"><Bell size={19} /><i /></button>
        <div className="header-avatar">JL</div>
      </div>
    </header>
  )
}

function MetricCard({ label, value, delta, icon: Icon, accent }: { label: string; value: string; delta: string; icon: typeof Users; accent: string }) {
  return (
    <div className="metric-card">
      <div className={`metric-icon ${accent}`}><Icon size={20} /></div>
      <div className="metric-heading"><span>{label}</span><MoreHorizontal size={17} /></div>
      <strong>{value}</strong>
      <p><b><ArrowUpRight size={13} />{delta}</b> from last month</p>
    </div>
  )
}

const flowRows = [
  { name: 'Comment “GUIDE” → Lead magnet', trigger: 'Instagram comment', channel: 'instagram', status: 'Live', runs: '2,481', rate: '78.4%', edited: '12 min ago' },
  { name: 'New follower welcome', trigger: 'New conversation', channel: 'telegram', status: 'Live', runs: '1,206', rate: '64.2%', edited: '2 hours ago' },
  { name: 'Course recommendation agent', trigger: 'Keyword: course', channel: 'telegram', status: 'Live', runs: '846', rate: '82.1%', edited: 'Yesterday' },
  { name: 'Abandoned inquiry follow-up', trigger: 'Contact tagged', channel: 'instagram', status: 'Draft', runs: '—', rate: '—', edited: 'Sep 1' },
]

function ChannelBadge({ type }: { type: string }) {
  return type === 'instagram'
    ? <span className="channel-pill ig"><Instagram size={13} /> Instagram</span>
    : <span className="channel-pill tg"><Telegram size={13} fill="currentColor" /> Telegram</span>
}

function Overview({ onMenu, goTo }: { onMenu: () => void; goTo: (v: View) => void }) {
  return (
    <div className="page-shell">
      <Header title="Good afternoon, Jordan" eyebrow="FRIDAY, SEPTEMBER 4" onMenu={onMenu} action={<button className="primary-btn" onClick={() => goTo('editor')}><Plus size={17} /> New automation</button>} />
      <main className="page-content overview">
        <section className="hero-strip">
          <div><span className="live-badge"><i /> ALL SYSTEMS OPERATIONAL</span><h2>Your automations are working.</h2><p>3,682 conversations handled in the last 30 days — without a contact tax.</p></div>
          <div className="hero-visual">
            <div className="orbit orbit-one" /><div className="orbit orbit-two" />
            <div className="hero-bubble bot-bubble"><Bot size={25} /></div>
            <div className="hero-bubble send-bubble"><Send size={18} fill="currentColor" /></div>
            <div className="hero-bubble check-bubble"><Check size={18} /></div>
          </div>
        </section>
        <section className="metrics-grid">
          <MetricCard label="Total contacts" value="12,849" delta="12.4%" icon={Users} accent="mint" />
          <MetricCard label="Conversations" value="3,682" delta="8.7%" icon={MessageSquareText} accent="purple" />
          <MetricCard label="AI resolution rate" value="74.8%" delta="5.2%" icon={Sparkles} accent="yellow" />
          <MetricCard label="AI cost this month" value="$3.42" delta="18.1%" icon={Zap} accent="blue" />
        </section>
        <section className="dashboard-grid">
          <div className="panel activity-panel">
            <div className="panel-header"><div><h3>Conversation activity</h3><p>Messages across all connected channels</p></div><button className="select-btn">Last 7 days <ChevronDown size={14} /></button></div>
            <div className="chart">
              <div className="chart-y"><span>800</span><span>600</span><span>400</span><span>200</span><span>0</span></div>
              <div className="chart-area">
                <div className="chart-gridlines"><i /><i /><i /><i /><i /></div>
                <svg viewBox="0 0 600 210" preserveAspectRatio="none">
                  <defs><linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#665cf6" stopOpacity=".25" /><stop offset="100%" stopColor="#665cf6" stopOpacity="0" /></linearGradient></defs>
                  <path className="area" d="M0,168 C38,155 60,162 86,137 S138,119 172,129 S218,92 258,103 S304,78 344,91 S392,53 430,67 S486,50 520,39 S568,24 600,31 L600,210 L0,210 Z" />
                  <path className="line" d="M0,168 C38,155 60,162 86,137 S138,119 172,129 S218,92 258,103 S304,78 344,91 S392,53 430,67 S486,50 520,39 S568,24 600,31" />
                  <circle cx="430" cy="67" r="5" />
                </svg>
                <div className="chart-labels"><span>Fri</span><span>Sat</span><span>Sun</span><span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span></div>
              </div>
            </div>
          </div>
          <div className="panel agent-panel">
            <div className="panel-header"><div><h3>AI agent performance</h3><p>This month</p></div><Sparkles size={18} className="purple-text" /></div>
            <div className="donut-wrap">
              <div className="donut"><div><strong>74.8%</strong><span>resolved</span></div></div>
              <div className="donut-legend"><p><i className="resolved" />Resolved by AI <b>1,842</b></p><p><i className="human" />Human handoff <b>621</b></p></div>
            </div>
            <div className="cost-row"><div><Zap size={16} /><span>Cost per AI resolution</span></div><strong>$0.0019</strong></div>
          </div>
        </section>
        <section className="panel automations-panel">
          <div className="panel-header"><div><h3>Top automations</h3><p>Your best-performing flows this month</p></div><button className="text-btn" onClick={() => goTo('flows')}>View all <ChevronRight size={15} /></button></div>
          <FlowTable rows={flowRows.slice(0, 3)} onOpen={() => goTo('editor')} compact />
        </section>
      </main>
    </div>
  )
}

function FlowTable({ rows, onOpen, compact = false }: { rows: typeof flowRows; onOpen: () => void; compact?: boolean }) {
  return (
    <div className="table-wrap">
      <table className="flow-table">
        <thead><tr><th>Automation</th><th>Channel</th><th>Status</th><th>Runs</th><th>Completion</th><th>Last edited</th><th /></tr></thead>
        <tbody>{rows.map((flow) => (
          <tr key={flow.name} onClick={onOpen}>
            <td><div className="flow-name"><span><GitBranch size={16} /></span><div><strong>{flow.name}</strong>{compact && <small>{flow.trigger}</small>}</div></div></td>
            <td><ChannelBadge type={flow.channel} /></td>
            <td><span className={`status ${flow.status.toLowerCase()}`}><i />{flow.status}</span></td>
            <td>{flow.runs}</td><td>{flow.rate}</td><td className="muted">{flow.edited}</td><td><MoreHorizontal size={17} /></td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  )
}

function Flows({ onMenu, goTo }: { onMenu: () => void; goTo: (v: View) => void }) {
  const [filter, setFilter] = useState('All')
  const visible = filter === 'All' ? flowRows : flowRows.filter((f) => f.status === filter)
  return (
    <div className="page-shell">
      <Header title="Automations" eyebrow="BUILD & MANAGE" onMenu={onMenu} action={<button className="primary-btn" onClick={() => goTo('editor')}><Plus size={17} /> New automation</button>} />
      <main className="page-content">
        <div className="section-intro"><div><h2>Turn conversations into outcomes</h2><p>Build visual flows that reply, qualify, and hand off — around the clock.</p></div></div>
        <div className="filter-bar">
          <div className="tabs">{['All', 'Live', 'Draft'].map((tab) => <button key={tab} className={filter === tab ? 'active' : ''} onClick={() => setFilter(tab)}>{tab}<span>{tab === 'All' ? 4 : tab === 'Live' ? 3 : 1}</span></button>)}</div>
          <div className="search-box"><Search size={16} /><input placeholder="Search automations" /></div>
        </div>
        <div className="panel flows-list"><FlowTable rows={visible} onOpen={() => goTo('editor')} /></div>
        <div className="template-heading"><div><h3>Start with a template</h3><p>Launch a proven automation, then make it yours.</p></div><button className="text-btn">Browse library <ChevronRight size={15} /></button></div>
        <div className="template-grid">
          <Template icon={AtSign} color="peach" title="Comment to DM" copy="Send a resource when someone comments a keyword." nodes="5 nodes" onClick={() => goTo('editor')} />
          <Template icon={Sparkles} color="lilac" title="AI lead qualifier" copy="Qualify intent, answer questions, and route hot leads." nodes="7 nodes" onClick={() => goTo('editor')} />
          <Template icon={MessageCircle} color="mint" title="Welcome sequence" copy="Greet new conversations and collect their goals." nodes="6 nodes" onClick={() => goTo('editor')} />
        </div>
      </main>
    </div>
  )
}

function Template({ icon: Icon, color, title, copy, nodes, onClick }: { icon: typeof AtSign; color: string; title: string; copy: string; nodes: string; onClick: () => void }) {
  return <button className="template-card" onClick={onClick}><div className={`template-icon ${color}`}><Icon size={20} /></div><div><h4>{title}</h4><p>{copy}</p><span>{nodes} <ArrowUpRight size={13} /></span></div></button>
}

type FlowData = { title: string; subtitle: string; icon: string; tone: string }
function FlowNode({ data, selected }: NodeProps) {
  const d = data as FlowData
  const icons: Record<string, React.ReactNode> = { trigger: <Hash size={17} />, send: <Send size={16} />, ai: <Sparkles size={17} />, condition: <GitBranch size={17} />, tag: <Tag size={17} />, handoff: <UserRound size={17} /> }
  return (
    <div className={`canvas-node ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Top} />
      <div className={`node-icon ${d.tone}`}>{icons[d.icon]}</div>
      <div><span>{d.title}</span><strong>{d.subtitle}</strong></div>
      <button><MoreHorizontal size={15} /></button>
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

const initialNodes = [
  { id: '1', type: 'flowNode', position: { x: 330, y: 25 }, data: { title: 'TRIGGER', subtitle: 'Comment contains “GUIDE”', icon: 'trigger', tone: 'peach' } },
  { id: '2', type: 'flowNode', position: { x: 330, y: 145 }, data: { title: 'SEND MESSAGE', subtitle: 'Hey {{first_name}} — here’s your guide!', icon: 'send', tone: 'blue' } },
  { id: '3', type: 'flowNode', position: { x: 330, y: 265 }, data: { title: 'AI AGENT', subtitle: 'Answer questions about the guide', icon: 'ai', tone: 'lilac' } },
  { id: '4', type: 'flowNode', position: { x: 330, y: 385 }, data: { title: 'CONDITION', subtitle: 'Interested in a consultation?', icon: 'condition', tone: 'yellow' } },
  { id: '5', type: 'flowNode', position: { x: 150, y: 525 }, data: { title: 'TAG CONTACT', subtitle: 'Add tag “Warm lead”', icon: 'tag', tone: 'mint' } },
  { id: '6', type: 'flowNode', position: { x: 510, y: 525 }, data: { title: 'HANDOFF', subtitle: 'Assign to human', icon: 'handoff', tone: 'rose' } },
]
const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', animated: true },
  { id: 'e2-3', source: '2', target: '3' },
  { id: 'e3-4', source: '3', target: '4' },
  { id: 'e4-5', source: '4', target: '5', label: 'NO' },
  { id: 'e4-6', source: '4', target: '6', label: 'YES' },
]

function FlowEditor({ onMenu, goTo }: { onMenu: () => void; goTo: (v: View) => void }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const [published, setPublished] = useState(false)
  const [palette, setPalette] = useState(true)
  const onConnect = useCallback((connection: Connection) => setEdges((eds) => addEdge(connection, eds)), [setEdges])
  const nodeTypes = useMemo(() => ({ flowNode: FlowNode }), [])
  return (
    <div className="editor-shell">
      <div className="editor-topbar">
        <button className="icon-btn mobile-menu" onClick={onMenu}><Menu size={20} /></button>
        <button className="back-btn" onClick={() => goTo('flows')}><ArrowLeft size={17} /></button>
        <div className="editor-title"><div><span>Comment “GUIDE” → Lead magnet</span><small><i /> Saved just now</small></div><button><ChevronDown size={14} /></button></div>
        <div className="editor-actions"><button className="secondary-btn"><Play size={15} /> Test flow</button><button className="primary-btn" onClick={() => { setPublished(true); setTimeout(() => setPublished(false), 2500) }}>{published ? <><Check size={16} /> Published</> : 'Publish changes'}</button></div>
      </div>
      <div className="editor-body">
        <aside className={`node-palette ${palette ? '' : 'closed'}`}>
          <div className="palette-heading"><div><h3>Nodes</h3><p>Drag onto the canvas</p></div><button className="icon-btn" onClick={() => setPalette(false)}><X size={17} /></button></div>
          <div className="search-box"><Search size={15} /><input placeholder="Search nodes" /></div>
          <p className="palette-label">MESSAGES</p>
          <PaletteItem icon={Send} tone="blue" title="Send message" copy="Text, media or quick replies" />
          <PaletteItem icon={Clock3} tone="gray" title="Delay" copy="Wait before continuing" />
          <PaletteItem icon={MessageSquareText} tone="cyan" title="Collect input" copy="Ask and save a response" />
          <p className="palette-label">LOGIC</p>
          <PaletteItem icon={GitBranch} tone="yellow" title="Condition" copy="Branch based on data" />
          <PaletteItem icon={Tag} tone="mint" title="Tag / Untag" copy="Organize a contact" />
          <p className="palette-label">INTELLIGENCE</p>
          <PaletteItem icon={Sparkles} tone="lilac" title="AI agent" copy="Handle a conversation" featured />
          <PaletteItem icon={UserRound} tone="rose" title="Human handoff" copy="Pause and assign" />
        </aside>
        {!palette && <button className="open-palette primary-btn" onClick={() => setPalette(true)}><Plus size={16} /> Add node</button>}
        <div className="flow-canvas">
          <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={onConnect} nodeTypes={nodeTypes} fitView fitViewOptions={{ padding: 0.16 }} minZoom={0.45} maxZoom={1.5}>
            <Background color="#d8d6e1" gap={22} size={1.2} />
            <Controls showInteractive={false} />
          </ReactFlow>
          <div className="canvas-status"><Radio size={13} /> Live on Instagram <span>•</span> 2,481 runs</div>
        </div>
      </div>
    </div>
  )
}

function PaletteItem({ icon: Icon, tone, title, copy, featured }: { icon: typeof Send; tone: string; title: string; copy: string; featured?: boolean }) {
  return <button className={`palette-item ${featured ? 'featured' : ''}`}><span className={tone}><Icon size={17} /></span><div><strong>{title}</strong><small>{copy}</small></div>{featured && <em>AI</em>}</button>
}

const conversations = [
  { name: 'Maya Chen', avatar: avatars.maya, text: 'That sounds perfect — can I book for...', time: '2m', unread: 2, channel: 'instagram', state: 'AI' },
  { name: 'Daniel Brooks', avatar: avatars.daniel, text: 'Thank you! I’ll check out the guide.', time: '18m', unread: 0, channel: 'telegram', state: 'AI' },
  { name: 'Elena Rossi', avatar: avatars.elena, text: 'I have a question about pricing.', time: '42m', unread: 1, channel: 'instagram', state: 'Human' },
  { name: 'Priya Shah', avatar: avatars.priya, text: 'Is this suitable for a small team?', time: '1h', unread: 0, channel: 'telegram', state: 'AI' },
]

function InboxPage({ onMenu }: { onMenu: () => void }) {
  const [selected, setSelected] = useState(0)
  const [message, setMessage] = useState('')
  const [sent, setSent] = useState<string[]>([])
  const [human, setHuman] = useState(false)
  const sendMessage = () => { if (message.trim()) { setSent((s) => [...s, message]); setMessage('') } }
  return (
    <div className="page-shell inbox-page">
      <Header title="Inbox" eyebrow="3 NEED YOUR ATTENTION" onMenu={onMenu} action={<button className="secondary-btn"><Settings size={16} /> Routing</button>} />
      <main className="inbox-layout">
        <aside className="conversation-list">
          <div className="inbox-tools"><div className="search-box"><Search size={16} /><input placeholder="Search conversations" /></div><button className="icon-btn"><Activity size={18} /></button></div>
          <div className="inbox-filters"><button className="active">All <span>12</span></button><button>Unread <span>3</span></button><button>Human <span>1</span></button></div>
          {conversations.map((c, index) => (
            <button key={c.name} className={`conversation-row ${selected === index ? 'active' : ''}`} onClick={() => setSelected(index)}>
              <div className="avatar-wrap"><img src={c.avatar} alt="" /><span className={c.channel}>{c.channel === 'instagram' ? <Instagram size={10} /> : <Telegram size={10} fill="currentColor" />}</span></div>
              <div className="conversation-copy"><div><strong>{c.name}</strong><time>{c.time}</time></div><p>{c.text}</p><small className={c.state === 'AI' ? 'ai-state' : 'human-state'}>{c.state === 'AI' ? <Sparkles size={10} /> : <UserRound size={10} />}{c.state === 'AI' ? 'AI handling' : 'Needs human'}</small></div>
              {c.unread > 0 && <em>{c.unread}</em>}
            </button>
          ))}
        </aside>
        <section className="chat-panel">
          <div className="chat-header">
            <div className="chat-person"><img src={avatars.maya} alt="" /><div><strong>Maya Chen</strong><span><i /> Active now · Instagram</span></div></div>
            <div><button className="secondary-btn" onClick={() => setHuman(!human)}>{human ? <><Sparkles size={15} /> Resume AI</> : <><UserRound size={15} /> Take over</>}</button><button className="icon-btn"><MoreHorizontal size={18} /></button></div>
          </div>
          <div className="chat-banner"><Sparkles size={15} /><span><b>AI agent is handling this conversation.</b> Using “Course Concierge” persona</span><button>View trace</button></div>
          <div className="messages">
            <div className="day-divider"><span>Today, 3:18 PM</span></div>
            <div className="message incoming">Hi! I saw your post about the creator systems guide. Could you send it to me?<time>3:18 PM</time></div>
            <div className="message outgoing">Absolutely, Maya! Here’s the <u>Creator Systems Guide</u> ✨<br /><br />What are you hoping to improve most — content planning, lead generation, or both?<time>3:18 PM · <Check size={12} /></time></div>
            <div className="message incoming">Mostly lead generation. I get engagement but struggle to turn it into calls.<time>3:20 PM</time></div>
            <div className="agent-thinking"><span><Sparkles size={13} /></span><div><strong>Agent used knowledge base</strong><p>Searched “lead generation consultation qualification” · 4 chunks</p></div><ChevronRight size={15} /></div>
            <div className="message outgoing">That’s exactly what the guide’s DM funnel covers. Based on what you shared, a quick strategy call could help map it to your audience.<br /><br />Would you like me to find a time this week?<time>3:21 PM · <Check size={12} /></time></div>
            <div className="message incoming">That sounds perfect — can I book for Thursday?<time>3:23 PM</time></div>
            {sent.map((text, i) => <div className="message outgoing" key={i}>{text}<time>Just now · <Check size={12} /></time></div>)}
          </div>
          <div className="composer">
            <div className="composer-mode">{human ? <><UserRound size={13} /> Replying as Jordan</> : <><Sparkles size={13} /> AI is replying</>}<ChevronDown size={13} /></div>
            <div className="composer-input"><button><Plus size={19} /></button><textarea value={message} onChange={(e) => setMessage(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }} placeholder={human ? 'Type your reply…' : 'Take over to send a reply…'} /><button className="send-btn" onClick={sendMessage}><Send size={16} fill="currentColor" /></button></div>
          </div>
        </section>
        <aside className="contact-panel">
          <div className="contact-profile"><img src={avatars.maya} alt="" /><h3>Maya Chen</h3><span>@mayamakes</span><button className="secondary-btn"><Instagram size={15} /> Open in Instagram</button></div>
          <div className="contact-section"><div className="section-label"><span>CONTACT</span><button><MoreHorizontal size={16} /></button></div><InfoRow label="Email" value="maya@studio.io" /><InfoRow label="Location" value="Vancouver, CA" /><InfoRow label="First seen" value="Aug 18, 2026" /></div>
          <div className="contact-section"><div className="section-label"><span>TAGS</span><button><Plus size={16} /></button></div><div className="tags"><span>Guide lead</span><span>Creator</span><span className="warm">Warm lead</span></div></div>
          <div className="contact-section agent-trace"><div className="section-label"><span>AGENT TRACE</span><button>View all</button></div>
            <div className="trace-line"><i /><div><strong>Knowledge search</strong><p>4 results · 312 tokens</p></div><time>3:21</time></div>
            <div className="trace-line"><i /><div><strong>Contact tagged</strong><p>Warm lead</p></div><time>3:21</time></div>
            <div className="trace-cost"><span>Conversation cost</span><strong>$0.0024</strong></div>
          </div>
        </aside>
      </main>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) { return <div className="info-row"><span>{label}</span><strong>{value}</strong></div> }

const contacts = [
  { name: 'Maya Chen', handle: '@mayamakes', avatar: avatars.maya, channel: 'instagram', tags: ['Guide lead', 'Warm lead'], state: 'Active', last: '2 min ago' },
  { name: 'Daniel Brooks', handle: '@dbrooks', avatar: avatars.daniel, channel: 'telegram', tags: ['Newsletter'], state: 'Active', last: '18 min ago' },
  { name: 'Elena Rossi', handle: '@elena.builds', avatar: avatars.elena, channel: 'instagram', tags: ['Pricing', 'Creator'], state: 'Active', last: '42 min ago' },
  { name: 'Priya Shah', handle: '@priyashah', avatar: avatars.priya, channel: 'telegram', tags: ['Course lead'], state: 'Active', last: '1 hour ago' },
]

function Contacts({ onMenu }: { onMenu: () => void }) {
  return (
    <div className="page-shell">
      <Header title="Contacts" eyebrow="12,849 PEOPLE" onMenu={onMenu} action={<button className="primary-btn"><Plus size={17} /> Add contact</button>} />
      <main className="page-content">
        <div className="section-intro"><div><h2>Your audience, in your database</h2><p>No contact limits. No surprise overage fees. Export anytime.</p></div><button className="secondary-btn"><ArrowUpRight size={16} /> Export CSV</button></div>
        <div className="contact-stats">
          <div><span>ALL CONTACTS</span><strong>12,849</strong><small>+418 this month</small></div>
          <div><span>SUBSCRIBED</span><strong>11,906</strong><small>92.7% of total</small></div>
          <div><span>NEW THIS WEEK</span><strong>128</strong><small>+14.2% vs last week</small></div>
        </div>
        <div className="filter-bar"><div className="search-box wide"><Search size={16} /><input placeholder="Search by name, handle, or tag" /></div><button className="select-btn"><Tag size={14} /> All tags <ChevronDown size={14} /></button><button className="select-btn"><Radio size={14} /> All channels <ChevronDown size={14} /></button></div>
        <div className="panel contacts-table-wrap"><table className="contacts-table"><thead><tr><th><input type="checkbox" /></th><th>Contact</th><th>Channel</th><th>Tags</th><th>Status</th><th>Last active</th><th /></tr></thead><tbody>
          {contacts.map((c) => <tr key={c.name}><td><input type="checkbox" /></td><td><div className="contact-cell"><img src={c.avatar} alt="" /><div><strong>{c.name}</strong><span>{c.handle}</span></div></div></td><td><ChannelBadge type={c.channel} /></td><td><div className="table-tags">{c.tags.map((t) => <span key={t}>{t}</span>)}</div></td><td><span className="status live"><i />{c.state}</span></td><td className="muted">{c.last}</td><td><MoreHorizontal size={17} /></td></tr>)}
        </tbody></table></div>
      </main>
    </div>
  )
}

function Knowledge({ onMenu }: { onMenu: () => void }) {
  const [uploaded, setUploaded] = useState(false)
  return (
    <div className="page-shell">
      <Header title="Knowledge" eyebrow="AI SOURCES" onMenu={onMenu} action={<button className="primary-btn" onClick={() => setUploaded(true)}><Plus size={17} /> Add source</button>} />
      <main className="page-content">
        <div className="section-intro"><div><h2>Give your agents the right answers</h2><p>Upload guides, FAQs, and product docs. Your data stays in your database.</p></div></div>
        <section className="knowledge-grid">
          <div className="upload-card" onClick={() => setUploaded(true)}><div><FileText size={24} /></div><h3>{uploaded ? 'Source added successfully' : 'Drop a file to train your agent'}</h3><p>{uploaded ? 'Your document is being chunked and indexed.' : 'PDF, DOCX, TXT, or Markdown · up to 25 MB'}</p><button className="secondary-btn">{uploaded ? <><Check size={16} /> Processing</> : 'Choose file'}</button></div>
          <div className="knowledge-summary"><div className="summary-icon"><Database size={21} /></div><div><span>KNOWLEDGE BASE</span><strong>1,284 chunks</strong><p>Across 4 indexed sources</p></div><div className="index-health"><i /><span>Healthy</span></div></div>
        </section>
        <div className="panel source-panel"><div className="panel-header"><div><h3>Sources</h3><p>Documents available to your AI agents</p></div><div className="search-box"><Search size={15} /><input placeholder="Search sources" /></div></div>
          {[
            ['Creator Systems Guide.pdf', 'PDF · 84 pages · 482 chunks', 'Updated Aug 30'],
            ['Consulting Offers FAQ.md', 'Markdown · 12 pages · 196 chunks', 'Updated Aug 28'],
            ['Course Curriculum.docx', 'Word · 36 pages · 374 chunks', 'Updated Aug 24'],
            ['Brand Voice & Tone.txt', 'Text · 8 pages · 232 chunks', 'Updated Aug 20'],
          ].map((doc) => <div className="source-row" key={doc[0]}><div className="file-icon"><FileText size={18} /></div><div><strong>{doc[0]}</strong><span>{doc[1]}</span></div><span className="indexed"><Check size={12} /> Indexed</span><time>{doc[2]}</time><button className="icon-btn"><MoreHorizontal size={17} /></button></div>)}
        </div>
      </main>
    </div>
  )
}

function App() {
  const [view, setView] = useState<View>('overview')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  return (
    <div className="app">
      {view !== 'editor' && <Sidebar view={view} setView={setView} open={sidebarOpen} setOpen={setSidebarOpen} />}
      <div className={view === 'editor' ? 'full-main' : 'main'}>
        {view === 'overview' && <Overview onMenu={() => setSidebarOpen(true)} goTo={setView} />}
        {view === 'flows' && <Flows onMenu={() => setSidebarOpen(true)} goTo={setView} />}
        {view === 'editor' && <FlowEditor onMenu={() => setSidebarOpen(true)} goTo={setView} />}
        {view === 'inbox' && <InboxPage onMenu={() => setSidebarOpen(true)} />}
        {view === 'contacts' && <Contacts onMenu={() => setSidebarOpen(true)} />}
        {view === 'knowledge' && <Knowledge onMenu={() => setSidebarOpen(true)} />}
      </div>
    </div>
  )
}

export default App
