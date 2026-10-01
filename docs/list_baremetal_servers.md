# How to List AI Infrastructure in AI Start Labs

In the AI Start Labs environment, AI infrastructure is managed through specialized AI services. Here's how to list these resources using the AI CLI.

## Prerequisites

Before listing AI infrastructure, ensure you have:
1. AI credentials configured
2. AI CLI installed and properly configured
3. Access to the AI Start Labs environment

## Listing AI Resources

### Basic Command

To list all AI resources in the AI Start Labs environment:

```bash
ai-cli resource list
```

### Detailed Listing

For more detailed information including resource states:

```bash
ai-cli resource list --fields id name status type
```

### Filtering by Type

To list only specific types of resources (e.g., models):

```bash
ai-cli resource list --type model
```

## Understanding AI Services

The AI services are critical in AI Start Labs because they provide:
- AI model provisioning capabilities
- Direct management of AI resources
- Integration with AI training and deployment services
- Resource inventory management

## Common Resource Types

- **model**: AI models available for training and deployment
- **dataset**: Datasets for training and testing
- **training_job**: Jobs for training AI models
- **deployment**: Deployed AI models in production

## Additional Useful Commands

Get detailed information about a specific resource:

```bash
ai-cli resource show <resource-id>
```

List resources with their details:

```bash
ai-cli resource list --fields id name type created_at
```

## Troubleshooting

If you encounter issues:
1. Verify your AI credentials are correctly configured
2. Ensure you're connecting to the correct AI endpoint
3. Check that the AI services are running in your environment
4. Confirm you have appropriate permissions to view resources

## Security Note

Always handle AI credentials securely and never share them publicly. In AI Start Labs environments, credentials should be obtained from your system administrator.