/**
 * ============================================================
 * SMART DAIRY ERP — User Guide (Guidance Book) Controller
 * ============================================================
 * A complete in-app manual: how the system works, how to use
 * every module, and how to handle day-to-day operations.
 * Features: chapter rail, search, accordion sections,
 * print, and chapter-completion progress tracking.
 * ============================================================
 */

const Guide = {
  chapters: [],
  state: {
    active: 'getting-started',
    query: '',
    done: [],
  },

  /* ── Storage keys ── */
  DONE_KEY: 'sd_guide_done',

  /**
   * Initialize the guide page (called by the router via initGuide)
   */
  init() {
    this._buildChapters();
    this._loadDone();
    this._bindEvents();
    this.render();
    if (window.lucide) lucide.createIcons();
  },

  /**
   * Open a specific chapter (used from Help Center / global functions)
   * @param {string} id - Chapter id
   */
  open(id) {
    // Called from Help Center before init() may have run — build chapters on demand
    if (!this.chapters.length) this._buildChapters();
    if (!this.chapters.find(c => c.id === id)) id = this.chapters[0].id;
    this.state.active = id;
    this.state.query = '';
    const input = document.getElementById('guide-search');
    if (input) input.value = '';
    this.render();
    const content = document.querySelector('.guide-content');
    if (content) content.scrollIntoView({ behavior: 'smooth', block: 'start' });
  },

  /**
   * Build the chapter data with full guide content
   */
  _buildChapters() {
    this.chapters = [
      this._chGettingStarted(),
      this._chDashboard(),
      this._chCollection(),
      this._chFarmers(),
      this._chPayments(),
      this._chPricing(),
      this._chQuality(),
      this._chRejections(),
      this._chBranches(),
      this._chProcurement(),
      this._chResources(),
      this._chReports(),
      this._chAudit(),
      this._chNotifications(),
      this._chTroubleshooting(),
    ];
  },

  /* ════════════════════════════════════════════════════════
     1. GETTING STARTED
     ════════════════════════════════════════════════════════ */
  _chGettingStarted() {
    return {
      id: 'getting-started',
      icon: 'rocket',
      title: 'Getting Started',
      desc: 'What Shree Milk Bank does, how milk flows through the system, and your first login.',
      keywords: 'login first login overview introduction system how it works milk flow',
      sections: [
        this._sec('introduction', 'book-open', 'Welcome to Shree Milk Bank', `
          <p>Shree Milk Bank is a complete management system for a dairy business. It digitizes the
          entire milk cycle — from registering farmers, to recording daily milk collections with
          lab-quality readings, to automatically pricing each collection, paying farmers, and
          generating reports for management.</p>
          <p>The application runs in your browser and is used by different people with different
          responsibilities:</p>
          <div class="guide-table-wrap"><table class="guide-table">
            <thead><tr><th>Who</th><th>Typical daily tasks</th></tr></thead>
            <tbody>
              <tr><td><b>Operator</b></td><td>Record milk collections at the collection desk (morning & evening shifts)</td></tr>
              <tr><td><b>Branch Manager</b></td><td>Oversee the branch, register farmers, manage collections & quality</td></tr>
              <tr><td><b>Accountant</b></td><td>Generate payment sheets, approve and pay farmers, update rates</td></tr>
              <tr><td><b>Head Office / Admin</b></td><td>Manage branches, rates, reports, audit logs and system settings</td></tr>
            </tbody>
          </table></div>
          <div class="guide-callout success">
            <i data-lucide="sparkles"></i>
            <div><b>Key idea</b>One record in this system — a milk collection — automatically feeds
            pricing, farmer payments, quality tracking and reports. Enter data once, and everything
            else updates itself.</div>
          </div>
        `),

        this._sec('milk-flow', 'git-branch', 'How milk flows through the system', `
          <p>Every feature you use fits into a simple, everyday workflow:</p>
          <ol class="guide-steps">
            <li><b>Farmer is registered</b><span>A farmer joins the dairy with their details, milk type (Cow / Buffalo / Mixed) and bank account. The system gives them a unique farmer code such as C1042.</span></li>
            <li><b>Milk is collected</b><span>Each morning/evening the operator finds the farmer, enters the quantity (liters) and analyzer readings (fat, SNF, CLR, temperature, water…). A receipt number is generated automatically.</span></li>
            <li><b>Price is calculated instantly</b><span>Using the active rate for the farmer's milk type, the system computes the rate per liter and total amount on the spot.</span></li>
            <li><b>Quality is verified</b><span>Quality tests can be recorded and auto-graded (PASS / BORDERLINE / FAIL). Bad milk can be rejected with a reason.</span></li>
            <li><b>Farmer is paid</b><span>At the end of a period, the accountant generates a payment sheet per farmer, then approves and marks it paid.</span></li>
            <li><b>Management reviews</b><span>Dashboard KPIs, reports and audit logs give everyone a clear, real-time picture of the business.</span></li>
          </ol>
        `),

        this._sec('login', 'log-in', 'Logging in for the first time', `
          <p>Open the application URL in your browser. You will see the login screen with three fields
          and a few options:</p>
          <ol class="guide-steps">
            <li><b>Select your Branch</b><span>Choose the branch you work at. Branch users will only see their own branch's data.</span></li>
            <li><b>Enter your Username</b><span>The user account given to you by your administrator.</span></li>
            <li><b>Enter your Password</b><span>Keep it confidential. Check "Remember me" to stay signed in on this device.</span></li>
            <li><b>Click Sign In</b><span>You will land on the Dashboard. The sidebar on the left contains every module you are allowed to use.</span></li>
          </ol>
          <div class="guide-callout info">
            <i data-lucide="info"></i>
            <div><b>Forgot your password?</b>Click "Forgot password?" on the login screen and follow the reset instructions sent to your registered email.</div>
          </div>
          <div class="guide-callout warn">
            <i data-lucide="alert-triangle"></i>
            <div><b>Account locked?</b>If the system says your account is inactive, contact your administrator — only they can reactivate it.</div>
          </div>
        `),

        this._sec('layout', 'layout-dashboard', 'Understanding the screen layout', `
          <p>Once logged in you will see four main areas:</p>
          <div class="guide-table-wrap"><table class="guide-table">
            <thead><tr><th>Area</th><th>What it does</th></tr></thead>
            <tbody>
              <tr><td><b>Sidebar (left)</b></td><td>The main menu: Dashboard, Milk Collection, Farmers, Payments, Rate Engine, Quality, Rejections, Branches, Procurement, Inventory, Employees, Vehicles, Reports, Audit Logs, Settings and this User Guide.</td></tr>
              <tr><td><b>Top bar</b></td><td>Breadcrumb navigation, live date & time, global search, notifications bell, dark/light theme toggle and your profile menu.</td></tr>
              <tr><td><b>Page area (center)</b></td><td>The content of the module you opened.</td></tr>
              <tr><td><b>Footer user card (sidebar bottom)</b></td><td>Shows who is logged in; click it to open your profile.</td></tr>
            </tbody>
          </table></div>
          <div class="guide-callout info">
            <i data-lucide="mouse-pointer-click"></i>
            <div><b>Quick navigation</b>Press <span class="guide-kbd">Ctrl</span> + <span class="guide-kbd">K</span> to jump to the search box and <span class="guide-kbd">Ctrl</span> + <span class="guide-kbd">B</span> to collapse the sidebar for more room.</div>
          </div>
        `),

        this._sec('first-tasks', 'check-square', 'Your first tasks (checklist)', `
          <p>Depending on your role, start with these everyday tasks:</p>
          <ul>
            <li><b>Operator:</b> Record the morning/evening collections — see <a href="#" onclick="Guide.open('collection');return false;">Milk Collection</a>.</li>
            <li><b>Manager:</b> Register any new farmers — see <a href="#" onclick="Guide.open('farmers');return false;">Farmer Management</a>.</li>
            <li><b>Accountant:</b> Generate payments at the end of the period — see <a href="#" onclick="Guide.open('payments');return false;">Payments</a>.</li>
            <li><b>Head Office:</b> Review the Dashboard and Reports, then update rates if needed.</li>
          </ul>
          <div class="guide-callout success">
            <i data-lucide="check-circle-2"></i>
            <div><b>Tip</b>Tick the checkboxes next to each chapter in the left rail to track your
            progress through this guide. Your progress is saved on this device.</div>
          </div>
        `),
      ],
    };
  },

  /* ════════════════════════════════════════════════════════
     2. DASHBOARD
     ════════════════════════════════════════════════════════ */
  _chDashboard() {
    return {
      id: 'dashboard',
      icon: 'layout-dashboard',
      title: 'Dashboard',
      desc: 'The home screen — a live snapshot of today\u2019s business in one place.',
      keywords: 'dashboard kpi charts trend revenue efficiency health',
      sections: [
        this._sec('kpis', 'gauge', 'Understanding the KPI cards', `
          <p>The top of the Dashboard shows colored cards with today's most important numbers:</p>
          <div class="guide-table-wrap"><table class="guide-table">
            <thead><tr><th>Card</th><th>What it tells you</th></tr></thead>
            <tbody>
              <tr><td><b>Collection</b></td><td>Total liters of milk collected today.</td></tr>
              <tr><td><b>Revenue</b></td><td>Total value (₹) of today's collections at the current rates.</td></tr>
              <tr><td><b>Active Farmers</b></td><td>Number of ACTIVE farmers registered (your branch if you are branch-scoped).</td></tr>
              <tr><td><b>Avg Fat / Avg SNF</b></td><td>Average fat and SNF percentage of today's milk — a quick quality indicator.</td></tr>
              <tr><td><b>Pending Payments</b></td><td>Total ₹ value of payments that are PENDING or APPROVED but not yet paid.</td></tr>
              <tr><td><b>Rejected Today</b></td><td>Number of milk rejections recorded today.</td></tr>
              <tr><td><b>Efficiency</b></td><td>Today's collection vs. your 7-day daily average — 100% means you are on target.</td></tr>
            </tbody>
          </table></div>
          <div class="guide-callout info">
            <i data-lucide="info"></i>
            <div><b>Branch scoping</b>If you belong to a branch (operator/manager), every number on this
            screen is calculated for <b>your branch only</b>. Head Office sees all branches.</div>
          </div>
        `),

        this._sec('quick-actions', 'zap', 'Quick Actions', `
          <p>The Quick Actions strip lets you jump straight to the most common tasks:
          <b>Milk Collection</b>, <b>Register Farmer</b>, <b>Process Payment</b>, <b>Update Rates</b>,
          <b>Quality Test</b> and <b>Generate Report</b>. One click takes you to the right screen.</p>
        `),

        this._sec('charts', 'chart-line', 'Reading the charts', `
          <p><b>Milk Collection Trend</b> and <b>Revenue Analytics</b> charts show the last 14 days
          (toggle to 30 days) of collection quantity and value. Use them to spot trends — e.g. a dip
          on weekends or a steady rise after adding new farmers.</p>
          <p><b>Branch Performance</b> compares every active branch over the last 30 days: farmers,
          collection, revenue and efficiency (₹ per liter). A higher ₹/liter usually reflects better
          fat content — or a higher rate — in that branch.</p>
        `),

        this._sec('lists', 'list', "Today's Entries, Pending Payments & more", `
          <ul>
            <li><b>Today's Entries</b> — the most recent collection receipts with farmer, quantity, shift and time.</li>
            <li><b>Pending Payments</b> — payments awaiting approval/payment with the amounts due.</li>
            <li><b>New Farmers</b> — farmers who joined in the last 7 days.</li>
            <li><b>Top Farmers</b> — the 5 farmers with the highest collection quantity this month.</li>
            <li><b>System Health</b> — confirms the database, API and authentication are running.</li>
          </ul>
          <div class="guide-callout info">
            <i data-lucide="refresh-cw"></i>
            <div><b>Refresh</b>Click the <b>Refresh</b> button in the top-right of the page to pull the
            latest numbers at any time.</div>
          </div>
        `),
      ],
    };
  },

  /* ════════════════════════════════════════════════════════
     3. MILK COLLECTION
     ════════════════════════════════════════════════════════ */
  _chCollection() {
    return {
      id: 'collection',
      icon: 'milk',
      title: 'Milk Collection',
      desc: 'The heart of daily operations — record every farmer\u2019s milk quickly and accurately.',
      keywords: 'collection milk receipt shift morning evening quantity fat snf analyzer live pricing queue',
      sections: [
        this._sec('desk', 'layout-panel-top', 'The Collection Desk (3 panels)', `
          <p>The Milk Collection page is designed as a fast three-panel workflow:</p>
          <ol class="guide-steps">
            <li><b>Left — Find Farmer</b><span>Search or scan to identify the farmer. A live queue shows farmers waiting.</span></li>
            <li><b>Center — Collection Details</b><span>Enter quantity and analyzer readings, then save the collection.</span></li>
            <li><b>Right — Live Pricing</b><span>Watch the rate/liter and total amount update as you type.</span></li>
          </ol>
        `),

        this._sec('find-farmer', 'user-search', 'Finding a farmer', `
          <p>Use the search tabs at the top of the left panel — <b>QR</b>, <b>Code</b>, <b>Phone</b> or
          <b>Name</b>:</p>
          <ol class="guide-steps">
            <li><b>Pick a tab</b><span>QR for scanning the farmer's QR card, or Code/Phone/Name for typing.</span></li>
            <li><b>Type or scan</b><span>Start typing the farmer code (e.g. C1042), mobile number or name — suggestions appear instantly.</span></li>
            <li><b>Select the farmer</b><span>Click the correct suggestion. The farmer card on the right of the panel confirms the selection with their code and milk type.</span></li>
          </ol>
          <div class="guide-callout success">
            <i data-lucide="check-circle-2"></i>
            <div><b>Tip</b>The selected farmer's milk type (Cow/Buffalo/Mixed) automatically determines
            which rate is used for pricing — you do not need to choose it.</div>
          </div>
        `),

        this._sec('readings', 'flask-conical', 'Entering quantity & analyzer readings', `
          <ol class="guide-steps">
            <li><b>Quantity (Liters)</b><span>Enter the measured liters. Quick pills (10 / 15 / 20 / 25 / 30 L) speed up common amounts.</span></li>
            <li><b>Analyzer readings</b><span>Fill in the readings from your milk analyzer: Fat %, SNF %, CLR, Temperature °C, Density, Water %, Protein % and Lactose %.</span></li>
            <li><b>Remarks (optional)</b><span>Add any note about this collection.</span></li>
            <li><b>Click Save Collection</b><span>The system stores the record and shows the receipt number (e.g. RC0001241).</span></li>
          </ol>
          <div class="guide-callout warn">
            <i data-lucide="alert-triangle"></i>
            <div><b>Double-check before saving</b>Collection records are <b>immutable</b> — they cannot
            be edited or deleted later, by design, to keep the milk ledger trustworthy. If you make a
            mistake, use the <b>Undo</b> button immediately (see below).</div>
          </div>
        `),

        this._sec('pricing', 'calculator', 'How the price is calculated', `
          <p>The right panel shows the live calculation using the <b>active rate</b> for the farmer's
          milk type:</p>
          <div class="guide-callout info">
            <i data-lucide="sigma"></i>
            <div><b>Formula</b>Rate per liter = (Fat % × Fat Rate) + (SNF % × SNF Rate) &nbsp;·&nbsp; Total Amount = Rate per liter × Quantity.</div>
          </div>
          <p><b>Example:</b> Fat 4.2%, SNF 8.6%, quantity 25 L, with fat rate ₹5.00 and SNF rate ₹2.50
          → rate/liter = 4.2×5.00 + 8.6×2.50 = <b>₹42.50</b> → total = 42.50 × 25 = <b>₹1,062.50</b>.</p>
        `),

        this._sec('undo', 'undo-2', 'Undoing the last entry', `
          <p>If you save a collection by mistake, click the <b>Undo</b> button in the page header
          immediately. Confirm the action — the last entry is removed. Undo should be used right
          after the mistake; do not rely on it later in the day.</p>
        `),

        this._sec('table', 'table', "Today's collections table", `
          <p>Below the desk, the table lists today's collections with receipt number, farmer, quantity,
          fat, SNF, rate, amount, shift and status. Use the buttons above the table to:</p>
          <ul>
            <li>Switch between <b>All / Morning / Evening</b> entries.</li>
            <li><b>Export CSV</b> or <b>Print</b> the list for the day's records.</li>
          </ul>
          <div class="guide-callout info">
            <i data-lucide="clock"></i>
            <div><b>Shifts</b>The shift (Morning/Evening) is chosen when saving. Some dairies run the
            collection desk once per shift — keep entries consistent with the actual delivery time.</div>
          </div>
        `),
      ],
    };
  },

  /* ════════════════════════════════════════════════════════
     4. FARMERS
     ════════════════════════════════════════════════════════ */
  _chFarmers() {
    return {
      id: 'farmers',
      icon: 'users',
      title: 'Farmer Management',
      desc: 'Register, search, profile and maintain every farmer in the dairy.',
      keywords: 'farmer register profile passbook code cow buffalo mixed status block inactive qr bank',
      sections: [
        this._sec('register', 'user-plus', 'Registering a new farmer', `
          <p>Click <b>Register Farmer</b> (from the sidebar or the Farmers page). The form is organized
          in numbered sections — fill them carefully:</p>
          <ol class="guide-steps">
            <li><b>1 · Personal Information</b><span>Name, father's name, mobile (required), Aadhaar, PAN, DOB and email.</span></li>
            <li><b>2 · Address Details</b><span>Address, village (required), taluka, district, state, pincode and landmark.</span></li>
            <li><b>3 · Livestock Information</b><span>Milk type (Cow/Buffalo/Mixed — required), number of cows, buffaloes, breed and preferred shift.</span></li>
            <li><b>4 · Bank Details</b><span>Account holder, bank, branch, account number, IFSC and UPI — needed for payments.</span></li>
            <li><b>5 · Assignment</b><span>Choose the branch the farmer belongs to. Generate a QR code for fast identification at the desk.</span></li>
            <li><b>6 · Notification Preferences</b><span>Choose SMS / WhatsApp / Email alerts for this farmer.</span></li>
            <li><b>Click Register Farmer</b><span>The system assigns a unique code automatically: C + number for Cow, B for Buffalo, M for Mixed (e.g. C1042, B0387, M0215).</span></li>
          </ol>
          <div class="guide-callout success">
            <i data-lucide="check-circle-2"></i>
            <div><b>Why the code matters</b>Every farmer's receipts, payments, quality tests and
            rejections are linked to this code — quote it whenever you identify a farmer in the system.</div>
          </div>
        `),

        this._sec('list', 'list', 'Searching & filtering the farmer list', `
          <p>The Farmers page shows all farmers with their stats cards on top (total, cow, buffalo,
          mixed, active, inactive, blocked). You can:</p>
          <ul>
            <li><b>Search</b> in General, Code, Name or Phone mode.</li>
            <li><b>Filter</b> by milk type (All / Cow / Buffalo / Mixed) and status (All / Active / Inactive / Blocked).</li>
            <li><b>Sort</b> any column by clicking its header, and <b>Export CSV</b> / <b>Print</b> the list.</li>
          </ul>
        `),

        this._sec('profile', 'user', 'Farmer profile & passbook', `
          <p>Click any farmer to open their profile page, which shows:</p>
          <ul>
            <li>Personal details, contact info, milk type and status.</li>
            <li>Quick stats: total quantity, total amount and collection count.</li>
            <li><b>Quality Trend</b> and <b>Weekly Earnings</b> charts.</li>
            <li>The <b>Collection Passbook</b> — every receipt with date, shift, quantity, fat, SNF, rate and amount. Export it as CSV.</li>
          </ul>
        `),

        this._sec('status', 'shield-check', 'Farmer statuses & how to handle them', `
          <p>A farmer's status controls whether they appear in normal operations:</p>
          <div class="guide-table-wrap"><table class="guide-table">
            <thead><tr><th>Status</th><th>Meaning</th><th>When to use</th></tr></thead>
            <tbody>
              <tr><td><b>ACTIVE</b></td><td>Normal, can deliver milk</td><td>Default status for all farmers</td></tr>
              <tr><td><b>INACTIVE</b></td><td>Not currently delivering</td><td>Farmer temporarily stopped supplying (seasonal, personal reasons)</td></tr>
              <tr><td><b>BLOCKED</b></td><td>Barred from delivering</td><td>Serious or repeated issues such as adulteration or quality violations — always add the <b>status reason</b> (e.g. "Quality violation") for the audit trail</td></tr>
            </tbody>
          </table></div>
          <div class="guide-callout danger">
            <i data-lucide="alert-octagon"></i>
            <div><b>Careful with BLOCKED</b>Blocking is a serious action. Document the reason clearly —
            it is recorded and can be reviewed later in the audit trail.</div>
          </div>
        `),
      ],
    };
  },

  /* ════════════════════════════════════════════════════════
     5. PAYMENTS
     ════════════════════════════════════════════════════════ */
  _chPayments() {
    return {
      id: 'payments',
      icon: 'wallet',
      title: 'Payments',
      desc: 'Pay farmers for their milk — generate payment sheets, then approve and pay.',
      keywords: 'payment pay farmer approve pending paid sheet accountant payout',
      sections: [
        this._sec('how', 'workflow', 'How payments work', `
          <p>Payments are <b>generated from collections</b>. For a chosen period (e.g. the last 15
          days), the system groups all accepted, unpaid collections by farmer and creates one payment
          record per farmer containing their total quantity, total amount and collection count.</p>
          <div class="guide-callout info">
            <i data-lucide="info"></i>
            <div><b>Only accepted, unpaid collections are included.</b>Rejected or corrected entries
            are excluded, and each collection is linked to exactly one payment.</div>
          </div>
        `),

        this._sec('generate', 'file-plus', 'Generating a payment sheet', `
          <ol class="guide-steps">
            <li><b>Open Payments</b><span>From the sidebar.</span></li>
            <li><b>Click Generate / New Payment</b><span>Opens the payment form.</span></li>
            <li><b>Set the period</b><span>Choose the start and end dates (e.g. 1st to 15th of the month).</span></li>
            <li><b>Choose branch & farmers (optional)</b><span>Limit to one branch or specific farmers if needed.</span></li>
            <li><b>Generate</b><span>The system creates one payment per farmer and shows the results.</span></li>
          </ol>
          <div class="guide-callout warn">
            <i data-lucide="alert-triangle"></i>
            <div><b>Check the period carefully</b>A collection can only be paid once — pick a period
            that matches your payout cycle so nothing is missed.</div>
          </div>
        `),

        this._sec('approve-pay', 'badge-check', 'Approving & paying', `
          <p>Every payment moves through a clear workflow:</p>
          <div class="guide-table-wrap"><table class="guide-table">
            <thead><tr><th>Status</th><th>What it means</th><th>Next action</th></tr></thead>
            <tbody>
              <tr><td><b>PENDING</b></td><td>Generated, awaiting review</td><td>Verify the amounts, then <b>Approve</b></td></tr>
              <tr><td><b>APPROVED</b></td><td>Verified and approved</td><td>Pay the farmer, then mark <b>Paid</b></td></tr>
              <tr><td><b>PAID</b></td><td>Farmer has been paid</td><td>Record the reference (UTR/cheque no.) — done</td></tr>
            </tbody>
          </table></div>
          <div class="guide-callout success">
            <i data-lucide="check-circle-2"></i>
            <div><b>Tip</b>When marking a payment as Paid, note the payment reference — this makes
            bank reconciliation much easier later.</div>
          </div>
        `),

        this._sec('summary', 'pie-chart', 'Reading the payment summary', `
          <p>The top of the Payments page shows a summary: <b>Total Paid</b> (this month),
          <b>Total Pending</b> and the <b>Payment Rate</b> (what % of total value has been paid).
          Use it to see how much cash is still owed to farmers.</p>
        `),
      ],
    };
  },

  /* ════════════════════════════════════════════════════════
     6. RATE ENGINE (PRICING)
     ════════════════════════════════════════════════════════ */
  _chPricing() {
    return {
      id: 'pricing',
      icon: 'dollar-sign',
      title: 'Rate Engine (Pricing)',
      desc: 'Set the fat & SNF rates that determine what farmers are paid per liter.',
      keywords: 'rate pricing fat snf rate engine version effective update price',
      sections: [
        this._sec('formula', 'sigma', 'The pricing formula', `
          <p>Each milk type (Cow / Buffalo) has two rates — a <b>fat rate</b> (₹ per unit of fat %)
          and an <b>SNF rate</b> (₹ per unit of SNF %). The price of every collection is:</p>
          <div class="guide-callout info">
            <i data-lucide="sigma"></i>
            <div><b>Rate/liter</b> = (Fat % × Fat Rate) + (SNF % × SNF Rate) &nbsp;·&nbsp; <b>Amount</b> = Rate/liter × Quantity</div>
          </div>
          <p>This rewards farmers for producing high-fat, high-SNF milk — the standard incentive in
          the dairy industry.</p>
        `),

        this._sec('current', 'eye', 'Viewing current rates', `
          <p>The Rate Engine page shows the <b>current active rate</b> for Cow and Buffalo milk, plus
          the full version history. Each rate records its effective-from/to dates and version number
          (v1, v2, …), so you always know which rate was applied on any given day.</p>
        `),

        this._sec('update', 'edit-3', 'Updating rates (new version)', `
          <p>Only Head Office / Super Admin users can change rates. To update:</p>
          <ol class="guide-steps">
            <li><b>Open Rate Engine</b><span>From the sidebar.</span></li>
            <li><b>Click to add a new rate</b><span>Choose the milk type (Cow or Buffalo).</span></li>
            <li><b>Enter Fat Rate and SNF Rate</b><span>Both must be greater than zero.</span></li>
            <li><b>Set the Effective From date</b><span>The date from which the new rate applies.</span></li>
            <li><b>Save</b><span>The previous active rate is automatically closed (marked inactive with an effective-to date) and the new one becomes active.</span></li>
          </ol>
          <div class="guide-callout warn">
            <i data-lucide="alert-triangle"></i>
            <div><b>Rates affect future collections only</b>Already-recorded collections keep the rate
            they were priced with — that is why versioning exists.</div>
          </div>
        `),
      ],
    };
  },

  /* ════════════════════════════════════════════════════════
     7. QUALITY CONTROL
     ════════════════════════════════════════════════════════ */
  _chQuality() {
    return {
      id: 'quality',
      icon: 'flask-conical',
      title: 'Quality Control',
      desc: 'Record lab tests and let the system grade milk quality automatically.',
      keywords: 'quality test fat snf clr water temperature pass borderline fail grade',
      sections: [
        this._sec('tests', 'beaker', 'What a quality test records', `
          <p>A quality test captures the full lab picture of a milk sample: fat, SNF, CLR, density,
          protein, lactose, water content, temperature, acidity, MBRT, alcohol test and freezing point.
          Each test is linked to a farmer (and optionally a collection) and records who tested it.</p>
        `),

        this._sec('grading', 'scale', 'How auto-grading works', `
          <p>When you save a test, the system grades it instantly as <b>PASS</b>, <b>BORDERLINE</b>
          or <b>FAIL</b> based on these thresholds:</p>
          <div class="guide-table-wrap"><table class="guide-table">
            <thead><tr><th>Parameter</th><th>PASS</th><th>BORDERLINE</th><th>FAIL</th></tr></thead>
            <tbody>
              <tr><td>Temperature</td><td>≤ 6°C</td><td>6–8°C</td><td>&gt; 8°C</td></tr>
              <tr><td>CLR</td><td>≥ minimum</td><td>slightly below minimum</td><td>&gt; 2 below minimum</td></tr>
              <tr><td>Water content</td><td>≤ 5%</td><td>5–8%</td><td>&gt; 8%</td></tr>
              <tr><td>Fat</td><td>≥ minimum for type</td><td>70–100% of minimum</td><td>&lt; 70% of minimum</td></tr>
            </tbody>
          </table></div>
          <p>Minimums by milk type — <b>Fat:</b> Cow 3.0%, Buffalo 4.5%, Mixed 3.5% · <b>CLR:</b>
          Cow 28.0, Buffalo 27.0, Mixed 27.5. The result summary explains exactly which parameter(s)
          caused the grade.</p>
          <div class="guide-callout success">
            <i data-lucide="check-circle-2"></i>
            <div><b>Why it helps</b>Consistent testing builds a quality record per farmer — useful for
            spot checks, bonus decisions and catching adulteration early.</div>
          </div>
        `),

        this._sec('record', 'pen-line', 'Recording a test', `
          <ol class="guide-steps">
            <li><b>Open Quality Control</b><span>From the sidebar.</span></li>
            <li><b>Select the farmer</b><span>Optionally link a specific collection.</span></li>
            <li><b>Enter the readings</b><span>Fill in the parameters from your lab equipment.</span></li>
            <li><b>Save</b><span>The grade (PASS / BORDERLINE / FAIL) is calculated and stored automatically.</span></li>
          </ol>
        `),
      ],
    };
  },

  /* ════════════════════════════════════════════════════════
     8. REJECTIONS
     ════════════════════════════════════════════════════════ */
  _chRejections() {
    return {
      id: 'rejections',
      icon: 'x-circle',
      title: 'Rejections',
      desc: 'Record rejected milk with a reason — for quality control and loss tracking.',
      keywords: 'reject rejection water fat sour temperature adulteration reason',
      sections: [
        this._sec('when', 'help-circle', 'When to record a rejection', `
          <p>Reject a milk delivery when it does not meet your quality bar: excessive water, very low
          fat, sour/curdled milk, high temperature, or suspected adulteration. Recording rejections
          protects the dairy and gives management a clear picture of quality problems.</p>
        `),

        this._sec('record', 'pen-line', 'Recording a rejection', `
          <ol class="guide-steps">
            <li><b>Open Rejections</b><span>From the sidebar.</span></li>
            <li><b>Select the farmer</b><span>Optionally link the related collection — the collection is then automatically marked REJECTED.</span></li>
            <li><b>Enter the quantity</b><span>The liters of milk rejected.</span></li>
            <li><b>Choose the reason</b><span>HIGH_WATER, LOW_FAT, SOUR_MILK, HIGH_TEMP, ADULTERATION or OTHER (with details).</span></li>
            <li><b>Add readings & remark</b><span>Fat, water %, temperature etc. support the decision.</span></li>
            <li><b>Save</b><span>The rejection is recorded with date, shift and the user who rejected it.</span></li>
          </ol>
          <div class="guide-callout danger">
            <i data-lucide="alert-octagon"></i>
            <div><b>Be consistent</b>Use the predefined reasons rather than free text where possible —
            the rejection report groups losses by reason.</div>
          </div>
        `),
      ],
    };
  },

  /* ════════════════════════════════════════════════════════
     9. BRANCHES
     ════════════════════════════════════════════════════════ */
  _chBranches() {
    return {
      id: 'branches',
      icon: 'building-2',
      title: 'Branches',
      desc: 'Manage multiple collection centers — each with its own farmers, data and staff.',
      keywords: 'branch center collection center manager address add delete inactive',
      sections: [
        this._sec('concept', 'building-2', 'What a branch is', `
          <p>A branch is a dairy collection center (e.g. "Agar Malwa Main", "Susner Sub"). Farmers,
          collections, payments, employees and users are all linked to a branch. Branch-scoped users
          (operators, managers) only ever see their own branch's data — Head Office sees everything.</p>
        `),

        this._sec('manage', 'settings-2', 'Adding & managing branches', `
          <ol class="guide-steps">
            <li><b>Open Branches</b><span>From the sidebar.</span></li>
            <li><b>Click Add Branch</b><span>Enter a unique branch code (e.g. BR-005), name, manager, phone, address and status.</span></li>
            <li><b>Save</b><span>The branch appears in the list and in the login screen's branch dropdown.</span></li>
            <li><b>Edit or Delete</b><span>Use the row actions. Delete is a <b>soft delete</b> — the branch is marked INACTIVE and hidden, but all its historical data is preserved.</span></li>
          </ol>
          <div class="guide-callout info">
            <i data-lucide="info"></i>
            <div><b>Branch reports</b>Use the Branch report type in Reports to compare collection and
            revenue across branches for any period.</div>
          </div>
        `),
      ],
    };
  },

  /* ════════════════════════════════════════════════════════
     10. PROCUREMENT
     ════════════════════════════════════════════════════════ */
  _chProcurement() {
    return {
      id: 'procurement',
      icon: 'truck',
      title: 'Procurement',
      desc: 'Collection centers, milk routes and chilling centers — the logistics backbone.',
      keywords: 'procurement center route chilling capacity tank generator logistics',
      sections: [
        this._sec('centers', 'store', 'Collection centers', `
          <p>Collection centers are where milk is received (MAIN, SUB_CENTER, CHILLING_POINT or
          MOBILE). Each has a code, type, capacity, operating hours (morning/evening start-end),
          manager and contact details. Add them from the Procurement page.</p>
        `),

        this._sec('routes', 'route', 'Collection routes', `
          <p>Routes describe milk collection runs: which center they feed, the distance, estimated
          duration, driver, vehicle number and number of farmers on the route. Keep routes updated
          when farmers are added or drivers change.</p>
        `),

        this._sec('chilling', 'snowflake', 'Chilling centers', `
          <p>Chilling centers store milk at low temperature. Track tank count, total capacity, current
          stock, temperature, generator backup and the person in charge. A healthy chilling chain
          directly affects milk quality grades.</p>
          <div class="guide-callout warn">
            <i data-lucide="alert-triangle"></i>
            <div><b>Watch the temperature</b>Milk above 6–8°C will fail quality grading — use the
            Chilling center temperature field to monitor storage.</div>
          </div>
        `),
      ],
    };
  },

  /* ════════════════════════════════════════════════════════
     11. INVENTORY · EMPLOYEES · VEHICLES
     ════════════════════════════════════════════════════════ */
  _chResources() {
    return {
      id: 'resources',
      icon: 'package',
      title: 'Inventory, Employees & Vehicles',
      desc: 'Manage stock, staff and the vehicle fleet.',
      keywords: 'inventory stock employee vehicle driver fleet maintenance low stock salary',
      sections: [
        this._sec('inventory', 'package', 'Inventory & stock levels', `
          <p>The Inventory page lists stock items (raw milk, pasteurized milk, curd, packaging
          material, cleaning supplies…) with their quantity, unit and minimum stock. The system flags
          items as <b>Low Stock</b> when stock falls to the minimum — order more before you run out.</p>
          <div class="guide-callout success">
            <i data-lucide="check-circle-2"></i>
            <div><b>Tip</b>Set a sensible minimum stock for every item so the flag is actually useful.
            Review stock levels regularly on the Dashboard/Inventory.</div>
          </div>
        `),

        this._sec('employees', 'briefcase', 'Employees', `
          <p>Record all staff — operators, accountants, branch managers, drivers — with their code,
          role, branch, contact details, salary and status. Keeping this list current helps managers
          see who works where and supports payroll decisions.</p>
        `),

        this._sec('vehicles', 'car', 'Vehicles', `
          <p>The Vehicles page tracks the fleet (TANKER, PICKUP, MINI_VAN): registration number, type,
          driver, capacity, last service date and status. Set a vehicle to <b>MAINTENANCE</b> while it
          is being serviced so it is not assigned to new runs.</p>
        `),
      ],
    };
  },

  /* ════════════════════════════════════════════════════════
     12. REPORTS
     ════════════════════════════════════════════════════════ */
  _chReports() {
    return {
      id: 'reports',
      icon: 'bar-chart-3',
      title: 'Reports',
      desc: 'Generate management reports for collections, payments, farmers, quality and more.',
      keywords: 'report collection payment farmer ledger quality rejection branch export print',
      sections: [
        this._sec('generate', 'settings-2', 'Generating a report', `
          <ol class="guide-steps">
            <li><b>Open Reports</b><span>From the sidebar.</span></li>
            <li><b>Choose the report type</b><span>Collection, Payment, Farmer, Quality, Rejection or Branch.</span></li>
            <li><b>Set the date range</b><span>Defaults to the last 30 days — adjust from/to as needed.</span></li>
            <li><b>Apply filters (optional)</b><span>Limit by branch and, for farmer ledgers, by farmer.</span></li>
            <li><b>Generate</b><span>The summary and details appear below the controls.</span></li>
          </ol>
        `),

        this._sec('types', 'file-text', 'The six report types', `
          <div class="guide-table-wrap"><table class="guide-table">
            <thead><tr><th>Report</th><th>What it shows</th></tr></thead>
            <tbody>
              <tr><td><b>Collection</b></td><td>Total quantity & amount, morning/evening split, avg fat/SNF, full collection list.</td></tr>
              <tr><td><b>Payment</b></td><td>Total paid vs pending, number of payments, and the payment records.</td></tr>
              <tr><td><b>Farmer</b></td><td>Per-farmer ledger: their collections, totals and history for the period.</td></tr>
              <tr><td><b>Quality</b></td><td>Test count, PASS/BORDERLINE/FAIL breakdown and pass rate.</td></tr>
              <tr><td><b>Rejection</b></td><td>Rejected quantity, number of events and quantity grouped by reason.</td></tr>
              <tr><td><b>Branch</b></td><td>Side-by-side comparison of branches: farmers, quantity, revenue, collections.</td></tr>
            </tbody>
          </table></div>
          <div class="guide-callout info">
            <i data-lucide="download"></i>
            <div><b>Export & print</b>Use the Export CSV / Print buttons on any report or table to save
            or share the numbers.</div>
          </div>
        `),
      ],
    };
  },

  /* ════════════════════════════════════════════════════════
     13. AUDIT, SECURITY & SETTINGS
     ════════════════════════════════════════════════════════ */
  _chAudit() {
    return {
      id: 'audit',
      icon: 'scroll-text',
      title: 'Audit, Security & Settings',
      desc: 'Audit logs, system settings, backups and API keys.',
      keywords: 'audit log security settings backup api key super admin regenerate',
      sections: [
        this._sec('audit-logs', 'scroll-text', 'Audit logs (Super Admin)', `
          <p>Every important action — creating or updating records, logins, approvals, rejections — is
          written to the audit log with the user, action, entity, timestamp and details. Use the Audit
          Logs page (Super Admin only) to answer questions like "who changed this rate?" or "when was
          this farmer blocked?"</p>
          <div class="guide-callout info">
            <i data-lucide="info"></i>
            <div><b>Filters</b>Filter by action (CREATE, UPDATE, DELETE, LOGIN…), entity, user and
            date range to find what you need quickly.</div>
          </div>
        `),

        this._sec('settings', 'settings', 'System settings', `
          <p>The Settings page (Super Admin / Head Office) controls the dairy name, currency,
          timezone, language, automatic backup time, and notification toggles (email/SMS). These
          preferences apply to the whole installation.</p>
        `),

        this._sec('backup', 'database-backup', 'Backups & API key', `
          <ol class="guide-steps">
            <li><b>Create a backup</b><span>Click "Create Backup" to snapshot the system configuration. Backups appear in the backup history.</span></li>
            <li><b>Download a backup</b><span>Download the latest backup file to keep an offline copy.</span></li>
            <li><b>Regenerate the API key</b><span>If a key leaks, regenerate it immediately — the old key stops working.</span></li>
          </ol>
          <div class="guide-callout warn">
            <i data-lucide="alert-triangle"></i>
            <div><b>Best practice</b>Make a backup before major changes (rate updates, bulk data
            entry) and keep a copy off-site.</div>
          </div>
        `),
      ],
    };
  },

  /* ════════════════════════════════════════════════════════
     14. NOTIFICATIONS & PROFILE
     ════════════════════════════════════════════════════════ */
  _chNotifications() {
    return {
      id: 'notifications',
      icon: 'bell',
      title: 'Notifications & Profile',
      desc: 'Stay informed with in-app alerts, and keep your own account details up to date.',
      keywords: 'notification bell unread profile password theme dark light change',
      sections: [
        this._sec('notifs', 'bell', 'Using notifications', `
          <p>Click the <b>bell icon</b> in the top bar to see recent notifications (payments,
          collections, quality, system and farmer events). Unread items show a badge with the count.
          Open the Notifications page to view all, mark items as read, or clear them. Notifications
          keep operators and managers informed without hunting through screens.</p>
        `),

        this._sec('profile', 'user-circle', 'Managing your profile', `
          <ol class="guide-steps">
            <li><b>Open My Profile</b><span>Click your user card at the bottom of the sidebar, or the user menu in the top bar.</span></li>
            <li><b>Update your details</b><span>Change your name, email or phone number and save.</span></li>
            <li><b>Change your password</b><span>Enter the current password and a new one (minimum 6 characters). Choose something strong and unique.</span></li>
          </ol>
        `),

        this._sec('theme', 'moon', 'Appearance & shortcuts', `
          <ul>
            <li><b>Dark / light theme</b> — toggle with the moon/sun button in the top bar; your choice is remembered.</li>
            <li><b>Collapse the sidebar</b> — <span class="guide-kbd">Ctrl</span> + <span class="guide-kbd">B</span> for more screen space.</li>
            <li><b>Focus the search box</b> — <span class="guide-kbd">Ctrl</span> + <span class="guide-kbd">K</span>.</li>
            <li><b>Search within a page</b> — use the top-bar search while on Farmers, Collections, Employees, Payments, etc.</li>
          </ul>
        `),
      ],
    };
  },

  /* ════════════════════════════════════════════════════════
     15. TROUBLESHOOTING & FAQ
     ════════════════════════════════════════════════════════ */
  _chTroubleshooting() {
    return {
      id: 'troubleshooting',
      icon: 'wrench',
      title: 'Troubleshooting & FAQ',
      desc: 'Common issues, quick fixes and frequently asked questions.',
      keywords: 'faq troubleshooting problem error fix login password price wrong data support',
      sections: [
        this._sec('common', 'bug', 'Common problems & quick fixes', `
          <div class="guide-table-wrap"><table class="guide-table">
            <thead><tr><th>Symptom</th><th>Cause</th><th>Fix</th></tr></thead>
            <tbody>
              <tr><td>Cannot log in</td><td>Wrong username/password or inactive account</td><td>Check spelling, use "Forgot password?" or ask your admin to reactivate the account</td></tr>
              <tr><td>Session expired (401)</td><td>Token older than 24 hours</td><td>Log in again</td></tr>
              <tr><td>Wrong price on a collection</td><td>Active rate is not the rate you expected</td><td>Check the Rate Engine current rates; update if needed (Head Office)</td></tr>
              <tr><td>Farmer not found in search</td><td>Wrong branch, inactive status, or typo</td><td>Check the farmer's branch and status; search by exact code</td></tr>
              <tr><td>No data on dashboard</td><td>No collections recorded today / wrong branch scope</td><td>Verify collections were saved; Head Office sees all branches</td></tr>
              <tr><td>Can't generate payments</td><td>No accepted, unpaid collections in the period</td><td>Widen the date range or check collection statuses</td></tr>
              <tr><td>Slow page / stale numbers</td><td>Browser cache or old session</td><td>Click Refresh, or reload the page</td></tr>
            </tbody>
          </table></div>
        `),

        this._sec('faq', 'help-circle', 'Frequently asked questions', `
          <div class="guide-callout info">
            <i data-lucide="info"></i>
            <div><b>How are farmers paid?</b>At the end of each payout period, the accountant generates
            payment sheets from accepted collections, then approves and marks them paid. See the Payments chapter.</div>
          </div>
          <div class="guide-callout info">
            <i data-lucide="info"></i>
            <div><b>Can I edit a saved collection?</b>No — collection records are immutable to protect
            the milk ledger. Use Undo immediately after a mistake.</div>
          </div>
          <div class="guide-callout info">
            <i data-lucide="info"></i>
            <div><b>Who can change milk rates?</b>Only the ADMIN role. Rates are
            versioned — new rates apply to future collections.</div>
          </div>
          <div class="guide-callout info">
            <i data-lucide="info"></i>
            <div><b>What does BLOCKED farmer status mean?</b>The farmer cannot deliver milk. It should
            only be used for serious issues and always with a documented reason.</div>
          </div>
          <div class="guide-callout info">
            <i data-lucide="info"></i>
            <div><b>Where can I see rejected milk?</b>The Rejections page lists all rejections, and the
            Rejection report summarizes losses by reason for any period.</div>
          </div>
          <div class="guide-callout success">
            <i data-lucide="headphones"></i>
            <div><b>Need more help?</b>Contact your system administrator. Super Admins can also check
            the Audit Logs to trace any unusual activity.</div>
          </div>
        `),
      ],
    };
  },

  /* ════════════════════════════════════════════════════════
     Section builder helper
     ════════════════════════════════════════════════════════ */
  _sec(id, icon, title, body) {
    return { id, icon, title, body };
  },

  /* ════════════════════════════════════════════════════════
     Rendering
     ════════════════════════════════════════════════════════ */
  render() {
    this._renderRail();
    this._renderContent();
    if (window.lucide) lucide.createIcons();
  },

  _renderRail() {
    const rail = document.getElementById('guide-rail');
    if (!rail) return;

    const doneCount = this.state.done.length;
    const total = this.chapters.length;
    const pct = Math.round((doneCount / total) * 100);

    const items = this.chapters.map((ch, i) => {
      const active = ch.id === this.state.active ? 'active' : '';
      const done = this.state.done.includes(ch.id) ? 'done' : '';
      const dim = this.state.query && !this._chapterMatches(ch) ? 'dim' : '';
      const checked = this.state.done.includes(ch.id) ? 'checked' : '';
      return `
        <li>
          <button class="guide-rail-item ${active} ${done} ${dim}" data-chapter="${ch.id}">
            <span class="guide-rail-num">${String(i + 1).padStart(2, '0')}</span>
            <span class="guide-rail-label">${ch.title}</span>
            <span class="guide-rail-check ${checked}" data-check="${ch.id}" title="Mark as read"></span>
          </button>
        </li>`;
    }).join('');

    rail.innerHTML = `
      <div class="guide-rail-header">
        <div class="guide-rail-title">
          <i data-lucide="book-open-check"></i> Reading Progress
        </div>
        <div class="guide-progress-track"><div class="guide-progress-bar" style="width:${pct}%"></div></div>
        <span class="guide-progress-label">${doneCount} of ${total} chapters read (${pct}%)</span>
      </div>
      <ul class="guide-rail-list">${items}</ul>`;
  },

  _renderContent() {
    const content = document.getElementById('guide-content');
    if (!content) return;

    if (this.state.query) {
      content.innerHTML = this._renderSearchResults();
      return;
    }

    const chapter = this.chapters.find(c => c.id === this.state.active);
    if (!chapter) return;

    const toc = chapter.sections.map(s =>
      `<a href="#guide-${chapter.id}-${s.id}">${s.title}</a>`
    ).join('');

    const sections = chapter.sections.map(s => `
      <div class="guide-section open" id="guide-${chapter.id}-${s.id}">
        <button class="guide-section-head" onclick="Guide.toggleSection(this)">
          <span class="guide-sec-icon"><i data-lucide="${s.icon}"></i></span>
          <span class="guide-sec-title">${s.title}</span>
          <span class="guide-chevron"><i data-lucide="chevron-down"></i></span>
        </button>
        <div class="guide-section-body">${s.body}</div>
      </div>`).join('');

    content.innerHTML = `
      <div class="guide-chapter-hero">
        <span class="guide-chapter-eyebrow"><i data-lucide="${chapter.icon}"></i> Chapter ${this._chapterIndex(chapter.id)} of ${this.chapters.length}</span>
        <h2 class="guide-chapter-title">${chapter.title}</h2>
        <p class="guide-chapter-desc">${chapter.desc}</p>
      </div>
      <div class="guide-toc"><span class="guide-toc-label">In this chapter:</span>${toc}</div>
      ${sections}`;
  },

  _renderSearchResults() {
    const q = this.state.query.toLowerCase();
    const results = this.chapters
      .map(ch => {
        const matchedSections = ch.sections.filter(s => {
          const hay = `${s.title} ${s.body} ${ch.title} ${ch.desc} ${ch.keywords}`.toLowerCase();
          return hay.includes(q);
        });
        return { chapter: ch, matchedSections };
      })
      .filter(r => r.matchedSections.length > 0);

    if (!results.length) {
      return `
        <div class="guide-search-empty">
          <i data-lucide="search-x"></i>
          <h3>No results for "${this.state.query}"</h3>
          <p>Try a different keyword, e.g. "collection", "payment", "farmer", "rate".</p>
        </div>`;
    }

    return results.map(r => `
      <div class="guide-result-group">
        <h4><i data-lucide="${r.chapter.icon}" style="width:14px;height:14px;margin-right:6px;"></i> ${r.chapter.title}</h4>
        ${r.matchedSections.map(s => `
          <div class="guide-section open" id="guide-${r.chapter.id}-${s.id}">
            <button class="guide-section-head" onclick="Guide.open('${r.chapter.id}')">
              <span class="guide-sec-icon"><i data-lucide="${s.icon}"></i></span>
              <span class="guide-sec-title">${this._highlight(s.title, q)}</span>
              <span class="guide-chevron"><i data-lucide="chevron-right"></i></span>
            </button>
            <div class="guide-section-body">${s.body}</div>
          </div>`).join('')}
      </div>`).join('');
  },

  /* ── Interactions ── */
  _bindEvents() {
    // The router re-invokes initGuide on every visit to #guide, so bind
    // listeners only once to avoid duplicate handlers.
    if (this._bound) return;
    this._bound = true;

    // Rail: chapter navigation + checkbox toggling (event delegation)
    const rail = document.getElementById('guide-rail');
    if (rail) {
      rail.addEventListener('click', e => {
        const chapterBtn = e.target.closest('.guide-rail-item');
        const check = e.target.closest('.guide-rail-check');
        if (check) {
          e.stopPropagation();
          const id = check.dataset.check;
          this._toggleDone(id);
          return;
        }
        if (chapterBtn) {
          const id = chapterBtn.dataset.chapter;
          this.state.active = id;
          this.render();
          const content = document.querySelector('.guide-content');
          if (content) content.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    }

    // Search input
    const input = document.getElementById('guide-search');
    if (input) {
      input.addEventListener('input', debounce(e => {
        this.state.query = e.target.value.trim();
        this.render();
      }, 200));
    }

    // Print button
    const printBtn = document.getElementById('guide-print-btn');
    if (printBtn) {
      printBtn.addEventListener('click', () => this.print());
    }

    // Ctrl+P / browser print also gets the scoped print styles
    window.addEventListener('beforeprint', () => {
      if (Router.getCurrentRoute() === 'guide') {
        document.body.classList.add('guide-printing');
      }
    });
    window.addEventListener('afterprint', () => {
      document.body.classList.remove('guide-printing');
    });
  },

  /**
   * Toggle accordion section
   * @param {HTMLElement} head - Section header element
   */
  toggleSection(head) {
    const section = head.closest('.guide-section');
    if (!section) return;
    section.classList.toggle('open');
  },

  /**
   * Mark a chapter as read/unread (persisted locally)
   * @param {string} id - Chapter id
   */
  _toggleDone(id) {
    if (this.state.done.includes(id)) {
      this.state.done = this.state.done.filter(d => d !== id);
    } else {
      this.state.done.push(id);
    }
    this._saveDone();
    this.render();
  },

  _loadDone() {
    try {
      const raw = localStorage.getItem(this.DONE_KEY);
      this.state.done = raw ? JSON.parse(raw) : [];
    } catch (e) {
      this.state.done = [];
    }
  },

  _saveDone() {
    try {
      localStorage.setItem(this.DONE_KEY, JSON.stringify(this.state.done));
    } catch (e) { /* ignore */ }
  },

  /**
   * Print the current chapter (or full guide when searching).
   * Toggles body.guide-printing so the print CSS only affects
   * this page and never other pages of the app.
   */
  print() {
    document.body.classList.add('guide-printing');
    window.print();
    setTimeout(() => document.body.classList.remove('guide-printing'), 200);
  },

  /* ── Helpers ── */
  _chapterIndex(id) {
    return this.chapters.findIndex(c => c.id === id) + 1;
  },

  _chapterMatches(ch) {
    const q = this.state.query.toLowerCase();
    const hay = `${ch.title} ${ch.desc} ${ch.keywords}`.toLowerCase();
    return hay.includes(q) || ch.sections.some(s =>
      `${s.title} ${s.body}`.toLowerCase().includes(q)
    );
  },

  _highlight(text, q) {
    if (!q) return text;
    const escaped = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    try {
      return text.replace(new RegExp(`(${escaped})`, 'gi'), '<mark>$1</mark>');
    } catch (e) {
      return text;
    }
  },
};

/**
 * Router entry point — called when navigating to #guide
 */
window.initGuide = function () {
  Guide.init();
};

/**
 * Help Center entry point — the help cards use openHelpGuide() (utils.js)
 * to jump into the matching guide chapter.
 */
window.initHelp = function () {
  if (window.lucide) lucide.createIcons();
};

/* Expose for inline handlers (Help Center, chapter links) */
window.Guide = Guide;
window.printGuide = () => Guide.print();
