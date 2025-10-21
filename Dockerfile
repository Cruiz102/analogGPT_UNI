FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg ca-certificates apt-transport-https dialog \
    apt-utils systemd \
  && rm -rf /var/lib/apt/lists/*

# Add Fortinet GPG key and apt source (same steps as screenshot)
RUN mkdir -p /usr/share/keyrings \
 && wget -qO - https://repo.fortinet.com/repo/forticlient/7.4/ubuntu22/DEB-GPG-KEY \
    | gpg --dearmor --yes -o /usr/share/keyrings/repo.fortinet.com.gpg \
 || (echo "Failed to fetch Fortinet key" && exit 1)

RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/repo.fortinet.com.gpg] https://repo.fortinet.com/repo/forticlient/7.4/ubuntu22/ stable non-free" \
    > /etc/apt/sources.list.d/repo.fortinet.com.list

RUN apt-get update && apt-get install -y --no-install-recommends forticlient \
  && rm -rf /var/lib/apt/lists/*

# Create non-root user (optional)
RUN useradd -m -s /bin/bash user

# Workdir and default user
WORKDIR /home/user
USER user
ENV HOME=/home/user

CMD ["/bin/bash"]

