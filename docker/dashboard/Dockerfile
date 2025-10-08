FROM node:20-bookworm-slim

WORKDIR /app

ENV NODE_ENV=production
ENV PNPM_HOME=/usr/local/share/pnpm
ENV PATH="${PNPM_HOME}:${PATH}"

RUN corepack enable

COPY dashboard/package.json dashboard/pnpm-lock.yaml ./ 
RUN pnpm install --frozen-lockfile

COPY dashboard .
RUN pnpm build

EXPOSE 3000

CMD ["pnpm", "start"]
