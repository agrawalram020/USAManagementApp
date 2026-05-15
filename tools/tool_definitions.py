ORCHESTRATOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "collect_academy_data",
            "description": (
                "Collect comprehensive data about the badminton academy including membership details, "
                "court utilization, revenue breakdown, coaching programs, operational costs, and "
                "customer demographics. Returns structured academy data for further analysis."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "data_categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Categories of data to collect. Options: 'memberships', 'court_utilization', "
                            "'revenue_streams', 'coaching', 'operations', 'demographics', 'facilities', 'pricing'"
                        )
                    },
                    "analysis_depth": {
                        "type": "string",
                        "enum": ["basic", "detailed", "comprehensive"],
                        "description": "Depth of data collection and analysis"
                    }
                },
                "required": ["data_categories", "analysis_depth"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_market",
            "description": (
                "Research the local badminton market including competitor pricing, market trends, "
                "corporate sports demand, demographic opportunities, and benchmarks. "
                "Returns market intelligence data."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "focus_areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Market areas to analyze. Options: 'competitors', 'pricing_benchmarks', "
                            "'corporate_demand', 'junior_sports', 'trends', 'demographics', 'underserved_segments'"
                        )
                    },
                    "academy_context": {
                        "type": "object",
                        "description": "Brief context about the academy location and current offerings",
                        "properties": {
                            "location": {"type": "string"},
                            "current_monthly_revenue": {"type": "number"},
                            "member_count": {"type": "integer"}
                        }
                    }
                },
                "required": ["focus_areas", "academy_context"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "identify_revenue_gaps",
            "description": (
                "Analyze academy data and market intelligence to identify specific revenue gaps, "
                "underperforming segments, missed opportunities, and quantify the potential upside "
                "for each gap. Returns prioritized list of revenue gaps with financial estimates."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "academy_data": {
                        "type": "object",
                        "description": "Structured academy data from collect_academy_data tool"
                    },
                    "market_data": {
                        "type": "object",
                        "description": "Market intelligence from analyze_market tool"
                    },
                    "gap_categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Categories to investigate. Options: 'pricing_gaps', 'utilization_gaps', "
                            "'program_gaps', 'segment_gaps', 'operational_gaps', 'partnership_gaps'"
                        )
                    }
                },
                "required": ["academy_data", "market_data", "gap_categories"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_revenue_strategy",
            "description": (
                "Create a comprehensive, prioritized revenue growth strategy with specific initiatives, "
                "implementation roadmaps, investment requirements, projected ROI, and a 12-month "
                "execution plan to close identified revenue gaps."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "revenue_gaps": {
                        "type": "object",
                        "description": "Prioritized revenue gaps from identify_revenue_gaps tool"
                    },
                    "academy_data": {
                        "type": "object",
                        "description": "Academy data for feasibility assessment"
                    },
                    "market_data": {
                        "type": "object",
                        "description": "Market data for competitive positioning"
                    },
                    "constraints": {
                        "type": "object",
                        "description": "Implementation constraints",
                        "properties": {
                            "budget_limit_inr": {"type": "number"},
                            "timeline_months": {"type": "integer"},
                            "priority": {
                                "type": "string",
                                "enum": ["quick_wins", "high_impact", "balanced"]
                            }
                        }
                    }
                },
                "required": ["revenue_gaps", "academy_data", "market_data", "constraints"]
            }
        }
    }
]
