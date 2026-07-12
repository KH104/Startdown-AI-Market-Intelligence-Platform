# StartDown - AI Market Intelligence Platform

AI-driven market intelligence and lead generation platform designed to help businesses discover, enrich, and act on high-potential sales leads and market insights.

## Features

- **Data Aggregation**: Collect business information from multiple sources
- **AI Enrichment**: Automatically fill in missing business details
- **Smart Lead Scoring**: ML-powered lead prioritization and ranking
- **Advanced Search**: Detailed filtering by various business criteria
- **Workflow Automation**: Export, outreach, alerts, and notifications
- **Analytics Dashboard**: Real-time insights and competitive intelligence


## Project Structure

```
startdown/
├── app/
│   ├── api/                    # API endpoints
│   │   ├── endpoints/          # Individual endpoint modules
│   │   └── router.py           # Main API router
│   ├── auth/                   # Authentication & security
│   ├── models/                 # Database models
│   ├── services/               # Business logic services
│   ├── config.py               # Configuration management
│   └── database.py             # Database setup
├── alembic/                    # Database migrations
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Development

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

### Environment Configuration

The application uses environment variables for configuration. See `.env.example` for all available options.

## License

MIT License
