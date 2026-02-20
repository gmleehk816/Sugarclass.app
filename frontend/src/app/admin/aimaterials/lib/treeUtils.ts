const IB_LEVELS = ['SL', 'HL'];

export const DATATREE: Record<string, Record<string, string[]>> = {
    "A-Level": {
        "Accounting": ["AQA Accounting (7127)", "CIE Accounting (9706)", "EDEXCEL Accounting (9AC0)"],
        "Biology": ["AQA Biology (7402)", "CIE Biology (9700)", "EDEXCEL Biology (9BI0)"],
        "Business": ["AQA Business (7132)", "CIE Business (9609)", "EDEXCEL Business (9BS0)"],
        "Chemistry": ["AQA Chemistry (7405)", "CIE Chemistry (9701)", "EDEXCEL Chemistry (9CH0)"],
        "Chinese": ["AQA Chinese (7679)", "CIE Chinese (9715)", "EDEXCEL Chinese (9CN0)"],
        "Computer Science": ["AQA Computer Science (7517)", "CIE Computer Science (9618)"],
        "Design Technology": ["AQA Design Technology (7552)", "CIE Design Technology (9705)", "EDEXCEL Design Technology Product Design (9DT0)"],
        "Economics": ["AQA Economics (7136)", "CIE Economics (9708)", "EDEXCEL Economics (9EC0)"],
        "English Language": ["AQA English Language (7702)", "CIE English Language (9093)", "EDEXCEL English Language (8EL0)"],
        "English Literature": ["AQA English Literature (7712)", "CIE Literature English (9695)", "EDEXCEL English Literature (9ET0)"],
        "French": ["AQA French (7652)", "CIE French (9716)", "EDEXCEL French (9FR0)"],
        "Further Mathematics": ["AQA Further Mathematics (7367)", "CIE Further Mathematics (9231)", "EDEXCEL Further Mathematics (9FM0)"],
        "Geography": ["AQA Geography (7037)", "CIE Geography (9696)", "EDEXCEL Geography (9GE0)"],
        "Global perspectives": ["CIE Global Perspectives Research (9239)"],
        "History": ["AQA History (7041)", "AQA History (7042)", "CIE History (9389)", "CIE History (9489)", "EDEXCEL History (9HI0)"],
        "Information Technology": ["AQA Information Technology (7527)", "CIE Information Technology (9626)", "EDEXCEL Information Technology (9IT0)"],
        "Mathematics": ["AQA Mathematics (7357)", "CIE Mathematics (9709)", "EDEXCEL Mathematics (9MA0)"],
        "Physical Education": ["AQA Physical Education (7582)", "CIE Physical Education (9396)", "EDEXCEL Physical Education (9PE0)"],
        "Physics": ["AQA Physics (7408)", "CIE Physics (9702)", "EDEXCEL Physics (9PH0)"],
        "Psychology": ["AQA Psychology (7182)", "CIE Psychology (9990)", "EDEXCEL Psychology (9PS0)"],
        "Sociology": ["AQA Sociology (7192)", "CIE Sociology (9699)", "EDEXCEL Sociology (9SC0)"],
    },
    "HKDSE": {
        "Biology": [], "Business, Accounting and Financial Studies": [], "Chemistry": [],
        "Chinese History": [], "Chinese Language": [], "Chinese Literature": [],
        "Citizenship and Social Development": [], "Design and Applied Technology": [],
        "Economics": [], "English Language": [], "Ethics and Religious Studies": [],
        "Geography": [], "Health Management and Social Care": [], "History": [],
        "Information and Communication Technology": [], "Literature in English": [],
        "Mathematics": [], "Music": [], "Physical Education": [], "Physics": [],
        "Technology and Living": [], "Tourism and Hospitality Studies": [], "Visual Arts": [],
    },
    "IB": {
        "Biology (100088)": IB_LEVELS,
        "Business Management (147712)": IB_LEVELS,
        "Chemistry (100113)": IB_LEVELS,
        "Chinese B Mandarin (117711)": IB_LEVELS,
        "Computer Science (100132)": IB_LEVELS,
        "Design Technology (100146)": IB_LEVELS,
        "Digital Societies (179711)": IB_LEVELS,
        "Economics (100164)": IB_LEVELS,
        "English A Language Literature (112733)": IB_LEVELS,
        "Environmental Systems Societies (100673)": IB_LEVELS,
        "Food Science and Technology (158711)": IB_LEVELS,
        "Geography (100222)": IB_LEVELS,
        "Global Politics (123711)": IB_LEVELS,
        "History (100680)": IB_LEVELS,
        "Mathematics AA (166711)": IB_LEVELS,
        "Music (100402)": IB_LEVELS,
        "Philosophy (100449)": IB_LEVELS,
        "Physics (100452)": IB_LEVELS,
        "Psychology (100474)": IB_LEVELS,
        "Social and Cultural Anthropology (100532)": IB_LEVELS,
        "Sports Exercise Health Science (100546)": IB_LEVELS,
        "Visual Arts (100608)": IB_LEVELS,
    },
    "IGCSE": {
        "Accounting": ["CIE Accounting (0452)", "EDEXCEL Accounting (4AC1)"],
        "Additional Mathematics": ["CIE Additional Mathematics (0606)", "EDEXCEL Further Pure Mathematics (4PM1)"],
        "Biology": ["CIE Biology (0610)", "EDEXCEL Biology (4BI1)"],
        "Business Studies": ["CIE Business (0450)", "EDEXCEL Business (4BS1)"],
        "Chemistry": ["CIE Chemistry (0620)", "EDEXCEL Chemistry (4CH1)"],
        "Chinese First Language": ["CIE Chinese First Language (0509)", "EDEXCEL Chinese (4CN0)"],
        "Chinese Mandarin Foreign Language": ["CIE Chinese Mandarin Foreign Language (0547)", "EDEXCEL Chinese (4CN0)"],
        "Chinese Second Language": ["CIE Chinese Second Language (0523)", "EDEXCEL Chinese (4CN0)"],
        "Combined Science": ["CIE Combined Science (0653)", "EDEXCEL Science (Double Award) (4SD1)"],
        "Commerce": ["CIE Commerce (0453)", "EDEXCEL Commerce (4CM1)"],
        "Computer Science": ["CIE Computer Science (0478)", "EDEXCEL Computer Science (4CP0)"],
        "Design Technology": ["CIE Design Technology (0445)"],
        "Economics": ["CIE Economics (0455)", "EDEXCEL Economics (4EC0)"],
        "English Literature": ["CIE Literature English (0475)", "EDEXCEL English literature (4ET1)"],
        "English Second Language": ["CIE English Second Language (0510)", "EDEXCEL English as a Second Language (4EA0)"],
        "Enterprise": ["CIE Enterprise (0454)"],
        "Environmental Management": ["CIE Environmental Management (0680)", "EDEXCEL Environmental Management (4ES0)"],
        "First Language English": ["CIE First Language English (0500)", "EDEXCEL English Language (4E1)"],
        "Food and Nutrition": ["CIE Food and Nutrition (0648)"],
        "Geography": ["CIE Geography (0460)", "EDEXCEL Geography (4GE0)"],
        "Global Perspectives": ["CIE Global Perspectives (0457)"],
        "History": ["CIE History (0470)", "EDEXCEL History (4HI0)"],
        "Human Biology": ["EDEXCEL Human Biology (4HB1)"],
        "ICT": ["CIE ICT (0417)", "EDEXCEL ICT (4IT0)"],
        "International Mathematics": ["CIE Mathematics - International (0607)", "EDEXCEL Mathematics (4MA0)"],
        "Mathematics": ["CIE Mathematics (0580)", "EDEXCEL Mathematics (4MA1)"],
        "Physical Education": ["CIE Physical Education (0413)"],
        "Physical Science": ["CIE Physical Science (0652)"],
        "Physics": ["CIE Physics (0625)", "EDEXCEL Physics (4PH1)"],
        "Psychology": ["CIE Psychology (0266)"],
        "Sociology": ["CIE Sociology (0495)"],
    },
    "primary": {
        "Year 1": [], "Year 2": [], "Year 3": [], "Year 4": [], "Year 5": [], "Year 6": [],
    },
    "secondary": {
        "Year 7": [], "Year 8": [], "Year 9": [],
    },
};

export type DbSubject = {
    id: string;
    name: string;
    syllabus_id: string;
    topic_count: number;
    subtopic_count: number;
    content_count: number;
};

// Helper: Sanitize string for matching (must match backend logic)
export function sanitizeId(name: string): string {
    return name.toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .replace(/[-\s]+/g, '_')
        .replace(/^_+|_+$/g, '')
        .substring(0, 50);
}

export function matchSubjectsToTree(dbSubjects: DbSubject[]) {
    const matched = new Set<string>();
    const subjectIdMap: Record<string, DbSubject> = {};

    // Build a lookup: subject ID -> DbSubject
    for (const sub of dbSubjects) {
        subjectIdMap[sub.id] = sub;
    }

    // Try to match each tree leaf to a DB subject
    const treeWithData: Record<string, Record<string, { boards: { name: string; dbSubject?: DbSubject }[]; dbSubject?: DbSubject }>> = {};

    for (const [level, subjects] of Object.entries(DATATREE)) {
        treeWithData[level] = {};
        const levelCode = sanitizeId(level || 'IGCSE');

        for (const [subjectName, boards] of Object.entries(subjects)) {
            const boardEntries = boards.map(boardName => {
                // For IB: board is "SL"/"HL", so ID = level_subject_board (e.g. "ib_biology_100088_sl")
                // For others: board is the full exam board name (e.g. "igcse_cie_physics_0625")
                const targetId = level === 'IB'
                    ? `${levelCode}_${sanitizeId(subjectName)}_${sanitizeId(boardName)}`
                    : `${levelCode}_${sanitizeId(boardName)}`;
                const db = subjectIdMap[targetId];
                if (db) matched.add(db.id);
                return { name: boardName, dbSubject: db };
            });

            const subjectId = `${levelCode}_${sanitizeId(subjectName)}`;
            const subjectDb = subjectIdMap[subjectId];
            if (subjectDb) matched.add(subjectDb.id);

            treeWithData[level][subjectName] = {
                boards: boardEntries,
                dbSubject: subjectDb,
            };
        }
    }

    const unmatched = dbSubjects.filter(s => !matched.has(s.id));

    return { treeWithData, unmatched };
}
