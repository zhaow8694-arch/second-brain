# High Risk Commands

The following commands must not run automatically. Queue them in APPROVAL_QUEUE.md first.

## Requires Approval

- `git push`
- `git push --tags`
- `gh pr create`
- `vercel deploy`
- `terraform apply`
- `kubectl apply`

## Forbidden By Default

- `rm -rf /`
- `sudo rm -rf`
- `cat ~/.ssh/*`
- `cat ~/.aws/*`
- `cat .env`
- `printenv`
- `terraform destroy`
- `kubectl delete`