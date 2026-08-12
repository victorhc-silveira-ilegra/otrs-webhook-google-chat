FROM centos:7 AS python-runtime

RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*.repo \
    && sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*.repo \
    && yum -y install wget tar gzip ca-certificates \
    && yum clean all

WORKDIR /opt
RUN wget -q -O python.tar.gz \
      "https://github.com/astral-sh/python-build-standalone/releases/download/20250317/cpython-3.13.2+20250317-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz" \
    && mkdir -p /opt/python \
    && tar xzf python.tar.gz -C /opt/python --strip-components=1 \
    && rm -f python.tar.gz

ENV PATH="/opt/python/bin:${PATH}"
WORKDIR /build
COPY app/pyproject.toml app/README.md /build/
COPY app/src /build/src
RUN pip install --no-cache-dir /build \
    && mkdir -p /opt/notifier/bin \
    && cp "$(command -v otrs-gchat-alert)" /opt/notifier/bin/otrs-gchat-alert

FROM centos:7

RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*.repo \
    && sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*.repo \
    && yum -y install epel-release \
    && yum -y update \
    && yum -y install \
        httpd \
        mod_ssl \
        mariadb \
        wget \
        tar \
        gzip \
        which \
        cronie \
        perl \
        perl-core \
        perl-DBD-MySQL \
        perl-JSON \
        perl-LDAP \
        perl-XML-LibXML \
        perl-XML-Parser \
        perl-Net-SSLeay \
        perl-YAML \
        perl-Encode-Locale \
        gd \
        gd-devel \
        libpng \
        libjpeg-turbo \
    && yum clean all

ENV OTRS_VERSION=3.2.1
WORKDIR /opt

RUN set -e; \
    if wget -O "otrs-${OTRS_VERSION}.tar.gz" "https://ftp.otrs.org/pub/otrs/otrs-${OTRS_VERSION}.tar.gz" \
      && test -s "otrs-${OTRS_VERSION}.tar.gz" \
      && tar xzf "otrs-${OTRS_VERSION}.tar.gz" \
      && test -d "otrs-${OTRS_VERSION}/scripts/database" \
      && test -f "otrs-${OTRS_VERSION}/scripts/database/otrs-schema.mysql.sql"; then \
      mv "otrs-${OTRS_VERSION}" otrs; \
      rm -f "otrs-${OTRS_VERSION}.tar.gz"; \
      useradd -r -d /opt/otrs -c 'OTRS user' otrs; \
      usermod -G apache otrs; \
      cd /opt/otrs; \
      cp Kernel/Config.pm.dist Kernel/Config.pm; \
      bin/otrs.SetPermissions.pl /opt/otrs --otrs-user=otrs --web-group=apache; \
    else \
      rm -f "otrs-${OTRS_VERSION}.tar.gz"; \
      rm -rf "otrs-${OTRS_VERSION}"; \
      mkdir -p /opt/otrs/Kernel/Config/Files \
        /opt/otrs/Kernel/System/Ticket/Event \
        /opt/otrs/var \
        /opt/otrs/bin; \
      useradd -r -d /opt/otrs -c 'OTRS user' otrs; \
      usermod -G apache otrs; \
      printf '%s\n' \
        'package Kernel::Config;' \
        'use strict;' \
        'use warnings;' \
        'sub Load {}' \
        'sub new { my ($$Type, %Param) = @_; my $$Self = {}; for (keys %Param) { $$Self->{$$_} = $$Param{$$_} } return bless $$Self, $$Type; }' \
        '1;' > /opt/otrs/Kernel/Config.pm; \
    fi

COPY --from=python-runtime /opt/python /opt/python
COPY --from=python-runtime /opt/notifier /opt/notifier
ENV PATH="/opt/python/bin:${PATH}"
ENV NOTIFIER_BIN=/opt/notifier/bin/otrs-gchat-alert
ENV WEBHOOK_URL=http://mock-webhook:8080/v1/spaces/POC/messages
ENV HTTP_TIMEOUT_SECONDS=10

COPY infra/docker/otrs/apache-otrs.conf /etc/httpd/conf.d/otrs.conf
COPY infra/docker/otrs/Kernel/System/Ticket/Event/GoogleChatAlert.pm /opt/otrs/Kernel/System/Ticket/Event/GoogleChatAlert.pm
COPY infra/docker/otrs/Kernel/Config/Files/GoogleChatAlert.xml /opt/otrs/Kernel/Config/Files/GoogleChatAlert.xml
COPY infra/docker/otrs/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && chmod +x /opt/notifier/bin/otrs-gchat-alert \
    && if [ -f /opt/otrs/scripts/apache2-httpd.include.conf ]; then \
         ln -sf /opt/otrs/scripts/apache2-httpd.include.conf /etc/httpd/conf.d/zzz-otrs.conf; \
       fi

EXPOSE 80
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["/usr/sbin/httpd", "-D", "FOREGROUND"]
