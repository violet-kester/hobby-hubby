# Render MCP Setup for Claude Code

This guide explains how to install and configure the Render MCP (Model Context Protocol) server for Claude Code, enabling direct management of Render services from Claude Code conversations.

## Prerequisites

- Claude Code CLI installed and configured
- A Render account (https://render.com)

## Step 1: Create Render API Key

1. Go to your Render Account Settings: https://dashboard.render.com/settings#api-keys
2. Click **"Create API Key"**
3. Give it a descriptive name (e.g., "Claude Code MCP")
4. Click **"Create"**
5. **Copy the API key immediately** - you won't be able to see it again!

**Security Note**: API keys grant access to all your Render workspaces and services. Store them securely and never commit them to version control.

## Step 2: Add Render MCP Server to Claude Code

Run the following command in your terminal:

```bash
claude mcp add --transport http render https://mcp.render.com/mcp \
  --header "Authorization: Bearer YOUR_API_KEY_HERE"
```

Replace `YOUR_API_KEY_HERE` with the API key you created in Step 1.

### Command Breakdown

- `claude mcp add` - Base command for adding MCP servers
- `--transport http` - Specifies this is a remote HTTP server
- `render` - Name for this MCP server (can be customized)
- `https://mcp.render.com/mcp` - Render's hosted MCP endpoint
- `--header "Authorization: Bearer ..."` - Authentication header with your API key

### Scope Options

By default, the server is added to the local project. You can change the scope with:

- `--scope local` - Only current directory (default)
- `--scope project` - Available throughout the current project
- `--scope user` - Available globally for your user account

Example with user scope:
```bash
claude mcp add --transport http render https://mcp.render.com/mcp \
  --header "Authorization: Bearer YOUR_API_KEY_HERE" \
  --scope user
```

## Step 3: Verify Installation

Check that the MCP server was added successfully:

```bash
claude mcp list
```

You should see `render` in the list of configured MCP servers with status information.

## Step 4: Set Active Workspace (In Claude Code)

Once the MCP is installed, you need to tell Claude Code which Render workspace to use. In a Claude Code conversation, simply ask:

```
Set my Render workspace to [your-workspace-name]
```

To find your workspace name:
1. Go to https://dashboard.render.com
2. Look at the workspace dropdown in the top-left corner

## What You Can Do With Render MCP

Once configured, Claude Code can:

- ✅ View your services, databases, and deployments
- ✅ Check deployment logs and service status
- ✅ Trigger manual deploys
- ✅ Monitor build progress
- ✅ View and manage environment variables
- ✅ Access database connection information
- ✅ Troubleshoot deployment issues

## Updating the API Key

If you need to rotate your API key or update the configuration:

1. Create a new API key in Render (Step 1)
2. Re-run the `claude mcp add` command with the new key
3. Delete the old API key from Render's dashboard

## Troubleshooting

### "Unknown option" error
Make sure you're using the correct syntax with `--transport http` before the server name.

### MCP server not responding
- Verify your API key is valid in Render's dashboard
- Check that the API key has the correct permissions
- Ensure you have an active internet connection

### Cannot access services
Make sure you've set your active workspace using the command in Step 4.

## Security Best Practices

1. **Never share your API key** in conversations, commits, or public channels
2. **Rotate keys regularly** for enhanced security
3. **Use workspace-specific keys** if possible
4. **Revoke unused keys** from your Render dashboard
5. **Store keys securely** using environment variables or secret managers

## Additional Resources

- Render MCP Documentation: https://render.com/docs/mcp-server
- Claude Code MCP Guide: https://code.claude.com/docs/en/mcp.md
- Render API Documentation: https://render.com/docs/api

## Configuration File Location

The MCP configuration is stored in:
- **Project scope**: `/path/to/project/.claude.json`
- **User scope**: `~/.claude.json`

You can manually edit these files if needed, but using the CLI is recommended.
