/* POLIS Case Study 2 — i18n string table (amendment 2026-08-28, v3.1).
   Display layer only. The participant-code prefix selects the language
   (SUZ -> zh-CN, LON/CHI -> en); every exported field name and value stays
   in the canonical English of schema case2-v3, so the data layer is
   untouched. `items` holds every UI string as {id, en, zh}; `stim.SUZ`
   holds display-layer zh renderings of the frozen SUZ stimulus texts
   (description.txt, trace.json chain and comprehension items), keyed so
   the frozen files themselves stay byte-identical. The review table
   protocols/resident_instrument_zh.csv is generated from this file
   (see CHANGELOG_amendment.md, v3.1). zh strings are faithful
   translations of the author-approved English (approved 2026-08-28
   12:26); they go live for the Suzhou arm once the PI confirms the
   translation table. */

window.CASE2_I18N = (function () {

  const items = {
    /* chrome */
    doc_title: { id: "UI-DOC-TITLE", en: "POLIS resident study",
      zh: "POLIS 居民研究" },
    brand: { id: "UI-BRAND", en: "POLIS resident participatory study",
      zh: "POLIS 居民参与式研究" },

    /* resume banner */
    resume_found_1: { id: "RESUME-01",
      en: "An unfinished session for participant code",
      zh: "在本设备上发现参与者编码" },
    resume_found_2: { id: "RESUME-02", en: "was found on this device.",
      zh: "的未完成会话。" },
    btn_resume: { id: "BTN-RESUME", en: "Resume where I left off",
      zh: "从上次中断处继续" },
    btn_startover: { id: "BTN-STARTOVER", en: "Discard and start over",
      zh: "放弃并重新开始" },

    /* participant information sheet (approved wording, 2026-08-28) */
    pis_title: { id: "PIS-TITLE", en: "Participant information sheet",
      zh: "参与者知情说明" },
    pis_intro: { id: "PIS-INTRO",
      en: "You are invited to take part in the POLIS resident participatory " +
        "study (Case Study 2), a fully online research session about how " +
        "needs for a local green space are expressed and recorded. Please " +
        "read this information sheet before deciding whether to take part.",
      zh: "诚邀您参加 POLIS 居民参与式研究(案例研究二)。这是一项完全在线进行" +
        "的研究会话,关注本地绿地需求如何被表达与记录。在决定是否参加之前," +
        "请先阅读本知情说明。" },
    pis_purpose_label: { id: "PIS-PURPOSE-LABEL", en: "Purpose:",
      zh: "目的:" },
    pis_purpose: { id: "PIS-PURPOSE",
      en: "This study tests whether residents and routine users of a local " +
        "green space can express and verify one place-based need more " +
        "faithfully through a map-based (POLIS spatial) channel than through " +
        "a conventional written channel, and whether the recorded link from " +
        "a confirmed need to a design decision is understandable. Results " +
        "are feasibility evidence for three study sites (Suzhou, London and " +
        "Chicago); they are not a citywide or official municipal " +
        "consultation.",
      zh: "本研究检验:本地绿地的居民与常态使用者,通过基于地图的(POLIS 空间)" +
        "渠道表达并核验一项与地点相关的需求,是否比通过常规文字渠道更加忠实;" +
        "以及从已确认需求到设计决策的记录链条是否可以被理解。研究结果仅作为" +
        "三个研究场地(苏州、伦敦、芝加哥)的可行性证据,不构成全市范围的征询," +
        "也不是官方的市政咨询。" },
    pis_procedure_label: { id: "PIS-PROCEDURE-LABEL", en: "Procedure:",
      zh: "流程:" },
    pis_procedure: { id: "PIS-PROCEDURE",
      en: "The session is fully online and takes about 30–60 minutes. After " +
        "you consent, you will: answer three short eligibility questions; " +
        "view a standard package about the study site; describe one need " +
        "for this place twice — once in a written form and once on a map, " +
        "in an order assigned by the study plan; after each, rate on a 1–7 " +
        "scale how faithfully the structured record captures your need, " +
        "then confirm, correct or reject that record; read a short record " +
        "trail showing how one need became a design decision and answer " +
        "four questions about it; and answer five short experience scales " +
        "plus an optional comment. Your answers are saved as one file that " +
        "you return to the study team.",
      zh: "本次会话完全在线进行,约需 30–60 分钟。同意参加后,您将:回答三道" +
        "简短的资格筛查题;查看关于研究场地的标准材料包;把您对这个地方的一项" +
        "需求表达两次——一次以文字形式、一次在地图上,顺序由研究方案指定;每次" +
        "表达后,以 1–7 分评价结构化记录对您需求的捕捉有多忠实,然后确认、更正" +
        "或拒绝该记录;阅读一段简短的记录链条,了解一项需求如何成为一项设计" +
        "决策,并回答四道相关问题;最后回答五条简短的体验量表和一条可选的开放" +
        "意见。您的回答将保存为一个文件,由您回传给研究团队。" },
    pis_voluntary_label: { id: "PIS-VOLUNTARY-LABEL",
      en: "Voluntary participation and compensation:",
      zh: "自愿参加与报酬:" },
    pis_voluntary: { id: "PIS-VOLUNTARY",
      en: "Taking part is voluntary and unpaid. You may stop at any time " +
        "without giving a reason and without any disadvantage; declining or " +
        "stopping does not affect any service you use. This is academic " +
        "research, not an official municipal consultation, and no design " +
        "shown here is a commitment to build.",
      zh: "参加本研究完全自愿,且不提供报酬。您可以随时停止,无需说明理由,也" +
        "不会因此受到任何不利影响;拒绝或中途退出不影响您使用任何服务。本研究" +
        "为学术研究,不是官方的市政咨询;这里展示的任何设计都不构成建设承诺。" },
    pis_data_label: { id: "PIS-DATA-LABEL", en: "Data handling:",
      zh: "数据处理:" },
    pis_data: { id: "PIS-DATA",
      en: "We collect only the minimum fields needed for this study: your " +
        "participant code, your screening answers, your two need " +
        "descriptions (text, and a map location within the site), your " +
        "ratings and answers, and the timing of the session pages. We do " +
        "not collect your name, exact address, full postcode/ZIP code, " +
        "precise home or work coordinates, or device identifiers. Responses " +
        "are stored under your participant code; the file linking codes to " +
        "contact details is held separately and is accessible only to the " +
        "named researchers. Your answers are saved as one file on your " +
        "device and returned by you to the study team, then kept read-only " +
        "in approved institutional storage. Resident data are never " +
        "uploaded to generative-AI or other unapproved external services, " +
        "and only fully anonymised, disclosure-reviewed results are " +
        "published.",
      zh: "我们只收集本研究所需的最少字段:您的参与者编码、筛查回答、两次需求" +
        "描述(文字,以及场地范围内的地图位置)、您的评分与作答,以及会话各页面" +
        "的时间信息。我们不收集您的姓名、确切住址、完整邮政编码、精确的住所或" +
        "工作地点坐标,也不收集设备标识信息。回答仅以参与者编码存储;编码与" +
        "联系方式的关联文件单独保存,仅限指定研究人员访问。您的回答将在您的" +
        "设备上保存为一个文件,由您回传研究团队,此后以只读方式保存在经批准的" +
        "机构存储中。居民数据绝不会上传到生成式人工智能或其他未经批准的外部" +
        "服务;仅发表经完全匿名化并通过披露审查的结果。" },
    pis_withdrawal_label: { id: "PIS-WITHDRAWAL-LABEL", en: "Withdrawal:",
      zh: "退出与撤回:" },
    pis_withdrawal: { id: "PIS-WITHDRAWAL",
      en: "You may stop the session at any time; an incomplete session is " +
        "not returned to the study team and is not analysed. An unfinished " +
        "session is kept only on this device so that you can resume it, and " +
        "you can discard it from the start page at any time; it is removed " +
        "from the device when you complete or discard the session. After " +
        "completing, you may withdraw your data within the approved " +
        "withdrawal window stated in your invitation by contacting the " +
        "study team with your participant code; the linkage file is then " +
        "used to locate and delete your records. Once data have been fully " +
        "anonymised they can no longer be traced to you and can then no " +
        "longer be withdrawn.",
      zh: "您可以随时停止会话;未完成的会话不会回传研究团队,也不会被纳入分析。" +
        "未完成的会话只保存在本设备上以便您继续作答,您随时可以在起始页放弃它;" +
        "会话完成或被放弃后,数据即从本设备移除。完成后,您可在邀请函所述的经" +
        "批准撤回时限内,凭参与者编码联系研究团队撤回数据;我们将通过关联文件" +
        "定位并删除您的记录。数据一经完全匿名化,即无法再追溯到您本人,此后将" +
        "无法撤回。" },
    pis_contacts_label: { id: "PIS-CONTACTS-LABEL", en: "Contacts:",
      zh: "联系方式:" },
    pis_contacts: { id: "PIS-CONTACTS",
      en: "For questions, withdrawal requests or concerns, contact the " +
        "study team through the contact route given in your invitation, " +
        "quoting your participant code. Concerns about the conduct of the " +
        "study may also be raised through the independent ethics contact " +
        "provided in the same invitation.",
      zh: "如有疑问、撤回请求或顾虑,请通过邀请函中提供的联系渠道联系研究团队," +
        "并注明您的参与者编码。对研究执行方式的顾虑,也可以通过同一邀请函中" +
        "提供的独立伦理联系渠道提出。" },

    /* consent + screener */
    consent_title: { id: "CONSENT-TITLE", en: "Consent and eligibility",
      zh: "同意参加与资格确认" },
    consent_intro: { id: "CONSENT-INTRO",
      en: "This online session takes about 30–60 minutes. You will describe " +
        "one need for a local green space in two ways, check how faithfully " +
        "each was recorded, read a short record trail, and answer a few " +
        "questions. Nothing shown here is a commitment to build. You can " +
        "stop at any time.",
      zh: "本次在线会话约需 30–60 分钟。您将以两种方式描述您对本地绿地的一项" +
        "需求,核对每次记录的忠实程度,阅读一段简短的记录链条,并回答几个问题。" +
        "这里展示的内容都不构成建设承诺。您可以随时停止。" },
    consent_read: { id: "CONSENT-READ",
      en: "I have read the participant information sheet above and I " +
        "consent to take part.",
      zh: "我已阅读上方的参与者知情说明,并同意参加。" },
    consent_adult: { id: "RES-S01-UI", en: "I am 18 or older.",
      zh: "我已年满 18 周岁。" },
    conn_label: { id: "RES-S02",
      en: "Which statement best describes your connection to the study area?",
      zh: "以下哪一项最能描述您与研究区域的关系?" },
    conn_resident: { id: "RES-S02-OPT-RESIDENT",
      en: "I usually live within 1 km of the study site (shown below)",
      zh: "我通常居住在研究场地周边 1 km 范围内(见下图)" },
    conn_routine: { id: "RES-S02-OPT-ROUTINE",
      en: "I have used the site or its immediately adjoining public space " +
        "at least once per month during the previous six months",
      zh: "过去六个月中,我每月至少一次使用该场地或与其紧邻的公共空间" },
    conn_neither: { id: "RES-S02-OPT-NEITHER", en: "Neither of these",
      zh: "两者都不是" },
    dup_label: { id: "RES-S03",
      en: "Have you previously consented to take part in this resident study?",
      zh: "您此前是否已同意参加过本居民研究?" },
    opt_choose: { id: "OPT-CHOOSE", en: "choose…", zh: "请选择……" },
    opt_no: { id: "OPT-NO", en: "No", zh: "否" },
    opt_yes: { id: "OPT-YES", en: "Yes", zh: "是" },
    consent_notteam: { id: "CONSENT-NOTTEAM",
      en: "I am not a member of the research or development team.",
      zh: "我不是本研究团队或开发团队的成员。" },
    code_label: { id: "CODE-LABEL",
      en: "Participant code (given to you by the study team):",
      zh: "参与者编码(由研究团队提供):" },
    code_ph: { id: "CODE-PH", en: "e.g. SUZ-P01", zh: "例如 SUZ-P01" },
    catchment_note: { id: "CATCHMENT-NOTE",
      en: "Eligibility area for this site: the shaded circle is the 1 km " +
        "catchment around the study site (dashed line = site boundary).",
      zh: "本场地的合格范围:阴影圆为以研究场地为中心的 1 km 范围圈(虚线为" +
        "场地边界)。" },
    btn_begin: { id: "BTN-BEGIN", en: "Begin", zh: "开始" },
    err_incomplete: { id: "ERR-INCOMPLETE",
      en: "Please complete every item, including your participant code.",
      zh: "请完成所有条目,包括填写您的参与者编码。" },
    err_unlisted: { id: "ERR-UNLISTED",
      en: "That participant code is not on the study list.",
      zh: "该参与者编码不在研究名单中。" },

    /* ineligible (approved wording, 2026-08-28) */
    inel_title: { id: "INEL-TITLE", en: "Thank you for your interest",
      zh: "感谢您的关注" },
    inel_body: { id: "INEL-BODY",
      en: "Based on your answers, this study can only include adults with a " +
        "residential or routine-use connection to the study site who have " +
        "not taken part before, so we cannot include you this time. No " +
        "study data about you has been stored.",
      zh: "根据您的回答,本研究只能纳入与研究场地存在居住或常态使用联系、且" +
        "此前未参加过本研究的成年人,因此本次无法邀请您参加。系统未存储任何" +
        "关于您的研究数据。" },

    /* site stimulus */
    site_title_SUZ: { id: "SITE-TITLE-SUZ", en: "The study site — Suzhou",
      zh: "研究场地——苏州" },
    site_title_LON: { id: "SITE-TITLE-LON", en: "The study site — London",
      zh: "研究场地——伦敦" },
    site_title_CHI: { id: "SITE-TITLE-CHI", en: "The study site — Chicago",
      zh: "研究场地——芝加哥" },
    site_map_alt: { id: "SITE-MAP-ALT", en: "standardised site map",
      zh: "标准化场地地图" },
    site_note: { id: "SITE-NOTE",
      en: "Take a moment to look at the site. When you are ready, continue. " +
        "You will describe <b>one</b> need or wish you have for this place " +
        "— the same need in two different ways.",
      zh: "请花一点时间了解该场地。准备好后请继续。您将描述您对这个地方的" +
        "<b>一项</b>需求或期望——同一项需求,用两种不同的方式表达。" },
    btn_continue: { id: "BTN-CONTINUE", en: "Continue", zh: "继续" },

    /* text mode */
    text_title: { id: "TEXT-TITLE", en: "Describe your need — written form",
      zh: "描述您的需求——文字形式" },
    text_prompt: { id: "RES-E01-UI",
      en: "In your own words: what should this place provide for you?",
      zh: "请用您自己的话说明:这个地方应当为您提供什么?" },
    text_ph: { id: "TEXT-PH",
      en: "e.g. I need a shaded place to sit while my children play…",
      zh: "例如:我需要一个有遮荫的座位处,孩子玩耍时我可以坐着看护……" },
    cat_label: { id: "CAT-LABEL", en: "Which category fits best?",
      zh: "哪一个类别最贴切?" },
    btn_submit: { id: "BTN-SUBMIT", en: "Submit", zh: "提交" },
    al_text_empty: { id: "AL-TEXT-EMPTY",
      en: "Please describe your need first.", zh: "请先描述您的需求。" },

    /* spatial mode */
    spatial_title: { id: "SPATIAL-TITLE", en: "Describe your need — on the map",
      zh: "描述您的需求——在地图上" },
    spatial_prompt: { id: "RES-E02-UI",
      en: "Click where your need belongs (dashed line = site, grey = " +
        "existing routes), then describe it.",
      zh: "请点击您的需求所在的位置(虚线为场地边界,灰色为现有路径),然后加以" +
        "描述。" },
    pin_none: { id: "PIN-NONE", en: "No location chosen yet — click the map.",
      zh: "尚未选择位置——请点击地图。" },
    pin_at: { id: "PIN-AT",
      en: "Location pinned at {lng}, {lat} — you can click again to move it.",
      zh: "已在 {lng}, {lat} 选定位置——再次点击可移动该位置。" },
    spatial_ph: { id: "SPATIAL-PH",
      en: "Describe the need at the pinned place…",
      zh: "请描述所选位置处的需求……" },
    al_pin_first: { id: "AL-PIN-FIRST",
      en: "Please click the map to pin a location first.",
      zh: "请先点击地图选定一个位置。" },
    al_spatial_empty: { id: "AL-SPATIAL-EMPTY",
      en: "Please describe the need at that place.",
      zh: "请描述该位置处的需求。" },

    /* need categories (display labels; exported values stay canonical) */
    cat_access: { id: "CAT-01", en: "access & mobility", zh: "通行与无障碍" },
    cat_shade: { id: "CAT-02", en: "shade & comfort", zh: "遮荫与舒适" },
    cat_play: { id: "CAT-03", en: "play & activity", zh: "游乐与活动" },
    cat_rest: { id: "CAT-04", en: "rest & seating", zh: "休憩与座椅" },
    cat_planting: { id: "CAT-05", en: "planting & nature", zh: "种植与自然" },
    cat_safety: { id: "CAT-06", en: "safety & lighting", zh: "安全与照明" },
    cat_other: { id: "CAT-07", en: "other", zh: "其他" },

    /* record check step A — fidelity */
    fid_title: { id: "FID-TITLE", en: "Here is what we recorded",
      zh: "这是我们记录到的内容" },
    fid_q: { id: "RES-F01-UI",
      en: "How faithfully does this record capture your need?",
      zh: "这份记录对您需求的捕捉有多忠实?" },
    fid_anchor: { id: "RES-F01-ANCHOR", en: "1 = not at all · 7 = fully",
      zh: "1 = 完全没有捕捉 · 7 = 完全捕捉" },
    fid_note: { id: "FID-NOTE",
      en: "Your rating is recorded before any correction. You will be able " +
        "to confirm, correct, or reject the record on the next screen.",
      zh: "您的评分会在任何更正之前先行记录。您将在下一屏确认、更正或拒绝该" +
        "记录。" },
    btn_fid: { id: "BTN-FID", en: "Record my rating", zh: "记录我的评分" },
    al_fid_required: { id: "AL-FID-REQUIRED",
      en: "Please rate how faithfully the record captures your need.",
      zh: "请先评价这份记录对您需求捕捉的忠实程度。" },

    /* structured record card */
    card_header: { id: "CARD-HEADER", en: "Your need, as recorded",
      zh: "您的需求(记录如下)" },
    card_category: { id: "CARD-CATEGORY", en: "category:", zh: "类别:" },
    card_place: { id: "CARD-PLACE", en: "place:", zh: "位置:" },
    card_forwhom: { id: "CARD-FORWHOM",
      en: "for whom: people like you who use this place — you can name " +
        "others in a correction",
      zh: "为谁:像您一样使用这个地方的人——您可以在更正中指出其他受益人" },
    card_noloc: { id: "CARD-NOLOC",
      en: "(no location captured in this channel)",
      zh: "(此渠道未采集位置)" },
    card_outside: { id: "CARD-OUTSIDE", en: " — outside the site boundary",
      zh: "——位于场地边界之外" },
    card_nearroute: { id: "CARD-NEARROUTE",
      en: " — about {m} m from an existing route",
      zh: "——距现有路径约 {m} 米" },

    /* record check step B — confirm / correct / reject */
    conf_title: { id: "CONF-TITLE", en: "Confirm, correct, or reject",
      zh: "确认、更正或拒绝" },
    fid_locked: { id: "FID-LOCKED",
      en: "Your fidelity rating of {v} / 7 has been recorded and can no " +
        "longer be changed.",
      zh: "您的保真度评分 {v} / 7 已记录,不能再更改。" },
    conf_q: { id: "RES-CF1-UI",
      en: "What would you like to do with this record?",
      zh: "您希望如何处理这份记录?" },
    opt_confirmed: { id: "RES-CF1-OPT-CONFIRM", en: "Confirm as recorded",
      zh: "确认记录无误" },
    opt_corrected: { id: "RES-CF1-OPT-CORRECT", en: "It needs correction",
      zh: "需要更正" },
    opt_rejected: { id: "RES-CF1-OPT-REJECT", en: "Reject this record",
      zh: "拒绝这份记录" },
    corr_q: { id: "RES-CF2",
      en: "Please state the correction needed.", zh: "请说明需要的更正。" },
    corr_note: { id: "RES-CF2-NOTE", en: "(one change per line)",
      zh: "(每行一条修改)" },
    al_conf_required: { id: "AL-CONF-REQUIRED",
      en: "Please choose confirm, correct, or reject.",
      zh: "请选择确认、更正或拒绝。" },
    al_cf2_required: { id: "AL-CF2-REQUIRED",
      en: "Please state the correction needed.", zh: "请说明需要的更正。" },

    /* provenance trace + comprehension */
    trace_title: { id: "TRACE-TITLE", en: "How a need becomes a decision",
      zh: "一项需求如何成为一项决策" },
    trace_intro: { id: "TRACE-INTRO",
      en: "Below is the real record trail for one need at this site — from " +
        "its source to the check after construction. Read it, then answer " +
        "four questions.",
      zh: "下面是该场地一项需求的真实记录链条——从其来源到建成后的核查。请阅读" +
        "后回答四道问题。" },
    al_trace_all4: { id: "AL-TRACE-ALL4",
      en: "Please answer all four questions.", zh: "请回答全部四道题。" },
    stage_source_evidence: { id: "STAGE-01", en: "source evidence",
      zh: "来源证据" },
    stage_encoded_need: { id: "STAGE-02", en: "encoded need", zh: "需求编码" },
    stage_arbitration_and_amendments: { id: "STAGE-03",
      en: "arbitration and amendments", zh: "仲裁与修正" },
    stage_design_synthesis: { id: "STAGE-04", en: "design synthesis",
      zh: "设计生成" },
    stage_final_geometry: { id: "STAGE-05", en: "final geometry",
      zh: "最终几何" },
    stage_regulatory_validation: { id: "STAGE-06",
      en: "regulatory validation", zh: "合规校验" },
    stage_implementation_review: { id: "STAGE-07",
      en: "implementation review", zh: "实施核查" },

    /* experience (RES-P01..P05, approved display wording) */
    exp_title: { id: "EXP-TITLE", en: "Your experience", zh: "您的体验" },
    exp_voice: { id: "RES-P01",
      en: "Through this process, my voice was heard.",
      zh: "通过这一过程,我的意见得到了听取。" },
    exp_fair: { id: "RES-P02", en: "The process treated my input fairly.",
      zh: "这一过程公正地对待了我的输入。" },
    exp_trust: { id: "RES-P03",
      en: "I would trust decisions recorded this way.",
      zh: "我会信任以这种方式记录的决策。" },
    exp_use: { id: "RES-P04", en: "The tools were easy to use.",
      zh: "这些工具易于使用。" },
    exp_burden: { id: "RES-P05", en: "The session felt burdensome.",
      zh: "这次会话让人感到负担。" },
    exp_comment_label: { id: "RES-O01-UI", en: "Anything else?",
      zh: "还有其他想说的吗?" },
    exp_comment_opt: { id: "RES-O01-OPT", en: "(optional)", zh: "(可选)" },
    btn_finish: { id: "BTN-FINISH", en: "Finish", zh: "完成" },
    al_exp_all: { id: "AL-EXP-ALL", en: "Please answer every scale.",
      zh: "请回答每一条量表。" },

    /* done + debrief (approved wording, 2026-08-28) */
    done_title: { id: "DONE-TITLE", en: "Thank you", zh: "感谢您" },
    debrief_body: { id: "DEBRIEF-BODY",
      en: "Thank you for taking part. This session tested how faithfully " +
        "two different channels record a resident's need for a local green " +
        "space; your ratings and any corrections are the study outcome, so " +
        "there are no right or wrong answers.",
      zh: "感谢您的参与。本次会话检验的是两种不同渠道对居民本地绿地需求记录的" +
        "忠实程度;您的评分和任何更正本身就是研究结果,因此不存在对错之分。" },
    debrief_note_label: { id: "DEBRIEF-NOTE-LABEL", en: "Please note:",
      zh: "请注意:" },
    debrief_note: { id: "DEBRIEF-NOTE",
      en: "no design shown in this study is a commitment to build, and " +
        "nothing you saw is promised for delivery.",
      zh: "本研究中展示的任何设计都不构成建设承诺,您所看到的内容均不保证会被" +
        "落实。" },
    done_code_1: { id: "DONE-CODE-1", en: "Your completion code is",
      zh: "您的完成编码为" },
    done_code_2: { id: "DONE-CODE-2", en: ".", zh: "。" },
    done_download: { id: "DONE-DOWNLOAD",
      en: "Your responses have been saved as a file download. If the " +
        "download did not start, use the button below, then send the file " +
        "to the study team.",
      zh: "您的回答已保存为一个下载文件。如果下载未自动开始,请使用下方按钮," +
        "然后将该文件发送给研究团队。" },
    btn_download: { id: "BTN-DOWNLOAD", en: "Download my responses",
      zh: "下载我的回答" },

    /* progress labels */
    step_consent: { id: "STEP-CONSENT", en: "1 / 8 · consent",
      zh: "1 / 8 · 同意参加" },
    step_site: { id: "STEP-SITE", en: "2 / 8 · the site",
      zh: "2 / 8 · 研究场地" },
    step_text_mode: { id: "STEP-TEXT", en: "needs · written",
      zh: "需求 · 文字" },
    step_spatial_mode: { id: "STEP-SPATIAL", en: "needs · on the map",
      zh: "需求 · 地图" },
    step_record_fidelity: { id: "STEP-FID", en: "record check · rating",
      zh: "记录核对 · 评分" },
    step_record_confirm: { id: "STEP-CONF", en: "record check · confirm",
      zh: "记录核对 · 确认" },
    step_trace: { id: "STEP-TRACE", en: "7 / 8 · record trail",
      zh: "7 / 8 · 记录链条" },
    step_experience: { id: "STEP-EXP", en: "8 / 8 · your experience",
      zh: "8 / 8 · 您的体验" },
    step_done: { id: "STEP-DONE", en: "complete", zh: "已完成" },
  };

  /* Display-layer zh renderings of the frozen SUZ stimulus texts.
     The frozen files (case2_interface/data/SUZ/*, case2_kit/stimuli/SUZ/*)
     stay byte-identical; identifiers, parameter names, values and hashes
     inside the records are kept verbatim. Comprehension option order and
     the exported keys/values (q1_source…q4_trigger, 0/1 coding) are
     unchanged — only the visible text is translated. */
  const stim = {
    SUZ: {
      description: {
        id: "STIM-SUZ-DESC",
        zh: "这是徐台路旁一处既有的社区绿地。地块以草地为主,点缀散生乔木,一侧" +
          "毗邻滨河绿带,其余侧临本地街道。周边住区的居民每天使用附近的人行道;" +
          "地块本身目前只有一个非正式出入口,内部没有园路。" },
      chain: [
        { id: "TRACE-SUZ-CHAIN-01",
          zh: "冻结世界模型 + 情景包 SUZ-GE-B(exp1 种子,冻结登记册)" },
        { id: "TRACE-SUZ-CHAIN-02",
          zh: "SUZ-N02:无障碍网络判定条件(clear_width >= 1.8 m,坡度 <= 1/48)" },
        { id: "TRACE-SUZ-CHAIN-03",
          zh: "AMD-2026-08-15-13;AMD-2026-08-15-14;AMD-2026-08-15-15;" +
            "AMD-2026-08-15-16" },
        { id: "TRACE-SUZ-CHAIN-04",
          zh: "SUZ-GE-B 的 POLIS 候选方案,由通用种子化构建器 " +
            "preregistration/build_polis_scenario.py 在分析机 Shapely 仿真路径" +
            "(AMD-2026-08-15-13)上生成;每情景独立几何(seed=SUZ-G" },
        { id: "TRACE-SUZ-CHAIN-05",
          zh: "POLIS:SUZ-GE-B:v1:path-upgrade:seg-001(clear_width_m=1.8," +
            "running_slope=0.02)" },
        { id: "TRACE-SUZ-CHAIN-06",
          zh: "design.gpkg accessible_network 完整状态:最小 clear_width_m=" +
            "1.800 m,最大 running_slope=0.02000,最大 cross_slope=0.01500 " +
            "<= 1/48,含全部 6 条路权支线/分支段(1763 m,AMD-2026-08-15-14" },
        { id: "TRACE-SUZ-CHAIN-07",
          zh: "导出 sha256 已登记(design.gpkg 已导出(sha256 8878f19321bd7695" +
            "bd5f29c6f476d5df7c2fccaad118011655c213be5deec...);竣工审计案例 " +
            "P1 依据 TOL-01 将实测 clear_width 与该登记参数进行比对" },
      ],
      comprehension: {
        q1_source: {
          id: "RES-Q01-SUZ",
          zh: "这条链条中已确认的需求最初来自哪里?",
          zh_options: [
            "设计开始前已记录的冻结证据登记册",
            "设计师的个人判断",
            "一次网络投票",
            "没有记录" ] },
        q2_decision: {
          id: "RES-Q02-SUZ",
          zh: "哪条已记录的决策将需求与设计联系起来?",
          zh_options: [
            "一条有文档记录的仲裁/修正记录",
            "一次非正式交谈",
            "没有任何决策记录",
            "一条社交媒体帖子" ] },
        q3_parameter: {
          id: "RES-Q03-SUZ",
          zh: "在最终几何中,哪个设计参数承载了这项需求?",
          zh_options: [
            "路径净宽(1.8 m)",
            "铺装的颜色",
            "公园的名称",
            "小汽车停车位数量" ] },
        q4_trigger: {
          id: "RES-Q04-SUZ",
          zh: "建成之后,什么情况会触发对这项决策的重新审查?",
          zh_options: [
            "实测值超出已登记容差的偏差",
            "天气变化",
            "任何情况都不会触发审查",
            "只有法院命令" ] },
      },
    },
  };

  const I = { items, stim, lang: "en" };

  I.langForCode = (code) =>
    /^SUZ/.test(String(code || "").trim().toUpperCase()) ? "zh" : "en";

  I.t = (key, params) => {
    const it = items[key];
    let s = it ? (it[I.lang] != null ? it[I.lang] : it.en) : key;
    if (params) for (const k of Object.keys(params))
      s = s.replaceAll(`{${k}}`, params[k]);
    return s;
  };

  I.apply = (lang) => {
    I.lang = lang === "zh" ? "zh" : "en";
    document.documentElement.lang = I.lang === "zh" ? "zh-CN" : "en";
    document.title = items.doc_title[I.lang];
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const it = items[el.dataset.i18n];
      if (it && it[I.lang] != null) el.innerHTML = it[I.lang];
    });
    document.querySelectorAll("[data-i18n-ph]").forEach((el) => {
      const it = items[el.dataset.i18nPh];
      if (it && it[I.lang] != null) el.placeholder = it[I.lang];
    });
    document.querySelectorAll("[data-i18n-alt]").forEach((el) => {
      const it = items[el.dataset.i18nAlt];
      if (it && it[I.lang] != null) el.alt = it[I.lang];
    });
  };

  /* zh display text for a frozen stimulus piece; null -> use frozen EN */
  I.stimText = (city, kind, arg) => {
    if (I.lang !== "zh" || !stim[city]) return null;
    const s = stim[city];
    if (kind === "description") return s.description.zh;
    if (kind === "chain") return s.chain[arg] ? s.chain[arg].zh : null;
    if (kind === "question")
      return s.comprehension[arg] ? s.comprehension[arg].zh : null;
    if (kind === "option") {
      const q = s.comprehension[arg.qid];
      return q && q.zh_options[arg.oi] != null ? q.zh_options[arg.oi] : null;
    }
    return null;
  };

  return I;
})();
