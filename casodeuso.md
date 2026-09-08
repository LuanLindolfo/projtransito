graph LR
    subgraph Sistema ["Auto Traffic Monitor (projtransito)"]
        UC1((UC01: Coletar Dados de Trânsito))
        UC2((UC02: Extrair Dados de Fonte Externa))
        UC3((UC03: Processar e Tratar Dados))
        UC4((UC04: Persistir Histórico))
        UC5((UC05: Notificar Erro / Alerta))
        UC6((UC06: Consultar Histórico))
    end

    Agendador["Agendador (GitHub Actions / Cron)"] --> UC1
    UC1 ..> UC2 : <<include>>
    UC1 ..> UC3 : <<include>>
    UC3 ..> UC4 : <<include>>
    UC3 ..> UC5 : <<extend>> (se houver falha/anomalia)
    
    Analista["Usuário / Analista"] --> UC6
