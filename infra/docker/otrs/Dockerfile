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
    OTRS_TGZ="otrs-${OTRS_VERSION}.tar.gz"; \
    rm -rf "otrs-${OTRS_VERSION}" otrs "${OTRS_TGZ}"; \
    for url in \
      "https://ftp.otrs.org/pub/otrs/${OTRS_TGZ}" \
      "https://download.znuny.org/releases/${OTRS_TGZ}"; do \
      echo "Baixando OTRS de ${url}"; \
      if wget -O "${OTRS_TGZ}" "${url}" \
        && test -s "${OTRS_TGZ}" \
        && tar xzf "${OTRS_TGZ}" \
        && test -d "otrs-${OTRS_VERSION}/bin/cgi-bin" \
        && test -f "otrs-${OTRS_VERSION}/bin/cgi-bin/index.pl" \
        && test -f "otrs-${OTRS_VERSION}/scripts/database/otrs-schema.mysql.sql"; then \
        break; \
      fi; \
      rm -f "${OTRS_TGZ}"; \
      rm -rf "otrs-${OTRS_VERSION}"; \
    done; \
    if [ ! -f "otrs-${OTRS_VERSION}/bin/cgi-bin/index.pl" ]; then \
      echo "Falha ao obter OTRS ${OTRS_VERSION} com cgi-bin/index.pl" >&2; \
      exit 1; \
    fi; \
    mv "otrs-${OTRS_VERSION}" otrs; \
    rm -f "${OTRS_TGZ}"; \
    useradd -r -d /opt/otrs -c 'OTRS user' otrs; \
    usermod -G apache otrs; \
    cd /opt/otrs; \
    cp Kernel/Config.pm.dist Kernel/Config.pm; \
    bin/otrs.SetPermissions.pl /opt/otrs --otrs-user=otrs --otrs-group=otrs --web-user=apache --web-group=apache

COPY --from=python-runtime /opt/python /opt/python
COPY --from=python-runtime /opt/notifier /opt/notifier
ENV PATH="/opt/python/bin:${PATH}"
ENV NOTIFIER_BIN=/opt/notifier/bin/otrs-gchat-alert
ENV GCHAT_WEBHOOK_URL=http://mock-webhook:8080/v1/spaces/POC/messages
ENV HTTP_TIMEOUT_SECONDS=10

COPY infra/docker/otrs/apache-otrs.conf /etc/httpd/conf.d/otrs.conf
COPY infra/docker/otrs/Kernel/System/Ticket/Event/GoogleChatAlert.pm /opt/otrs/Kernel/System/Ticket/Event/GoogleChatAlert.pm
COPY infra/docker/otrs/Kernel/Config/Files/GoogleChatAlert.xml /opt/otrs/Kernel/Config/Files/GoogleChatAlert.xml
COPY infra/docker/otrs/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && chmod +x /opt/notifier/bin/otrs-gchat-alert \
    && rm -f /etc/httpd/conf.d/zzz-otrs.conf

EXPOSE 80
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["/usr/sbin/httpd", "-D", "FOREGROUND"]
