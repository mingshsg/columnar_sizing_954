# Configuration reference: Elasticsearch 9.5.5 benchmark

Captured from the live cluster after the load and verify stages. Effective values come from `GET <data stream>/_settings?include_defaults=true`. Full JSON for every data stream is in the collapsible sections below.

## Comparison of effective settings

| Setting | `logs-otel.logsdb-bench` | `logs-otel.columnar-bench` | `traces-otel.logsdb-bench` | `traces-otel.columnar-bench` | `metrics-otel.tsds-bench` |
|---|---|---|---|---|---|
| index.mode | logsdb | logsdb_columnar | logsdb | logsdb_columnar | time_series |
| source.mode | synthetic | synthetic | synthetic | synthetic | synthetic |
| shards | 2 | 2 | 2 | 2 | 2 |
| codec | best_compression | best_compression | best_compression | best_compression | default |
| sort | host.name, @timestamp | host.name, @timestamp | host.name, @timestamp | host.name, @timestamp | _tsid, @timestamp |
| routing_path | - | - | - | - | resource.attributes.service.name, resource.attributes.host.name, resource.attributes.k8s.pod.name, resource.attributes.k8s.namespace.name, resource.attributes.cloud.region, attributes.stream |
| look_back_time | 2h | 2h | 2h | 2h | 7d |

Replicas: 0 for all data streams. The logs and traces columnar streams use `index.mode: logsdb_columnar`; the logsdb streams use `logsdb`; metrics uses `time_series`.

## `logs-otel.logsdb-bench`

### Index template (`bench-logs-otel.logsdb-bench`)

<details><summary>JSON</summary>

```json
{
  "index_templates": [
    {
      "index_template": {
        "_meta": {
          "benchmark": "otel-es-benchmark",
          "signal": "logs"
        },
        "composed_of": [],
        "created_date_millis": 1792673929542,
        "data_stream": {
          "allow_custom_routing": false,
          "hidden": false
        },
        "index_patterns": [
          "logs-otel.logsdb-bench"
        ],
        "modified_date_millis": 1792673929542,
        "priority": 500,
        "template": {
          "mappings": {
            "dynamic": "strict",
            "properties": {
              "@timestamp": {
                "type": "date"
              },
              "attributes": {
                "properties": {
                  "app.cart.items": {
                    "type": "integer"
                  },
                  "app.order.id": {
                    "type": "keyword"
                  },
                  "exception.message": {
                    "type": "match_only_text"
                  },
                  "exception.type": {
                    "type": "keyword"
                  },
                  "http.request.method": {
                    "type": "keyword"
                  },
                  "http.response.status_code": {
                    "type": "long"
                  },
                  "thread.name": {
                    "type": "keyword"
                  },
                  "url.path": {
                    "type": "keyword"
                  }
                }
              },
              "body": {
                "properties": {
                  "text": {
                    "type": "match_only_text"
                  }
                }
              },
              "observed_timestamp": {
                "type": "date"
              },
              "resource": {
                "properties": {
                  "attributes": {
                    "properties": {
                      "cloud.region": {
                        "type": "keyword"
                      },
                      "deployment.environment.name": {
                        "type": "keyword"
                      },
                      "host.name": {
                        "type": "keyword"
                      },
                      "k8s.namespace.name": {
                        "type": "keyword"
                      },
                      "k8s.pod.name": {
                        "type": "keyword"
                      },
                      "service.name": {
                        "type": "keyword"
                      },
                      "service.version": {
                        "type": "keyword"
                      }
                    }
                  }
                }
              },
              "scope": {
                "properties": {
                  "name": {
                    "type": "keyword"
                  },
                  "version": {
                    "type": "keyword"
                  }
                }
              },
              "severity_number": {
                "type": "integer"
              },
              "severity_text": {
                "type": "keyword"
              },
              "span_id": {
                "type": "keyword"
              },
              "trace_id": {
                "type": "keyword"
              }
            }
          },
          "settings": {
            "index": {
              "mapping": {
                "source": {
                  "mode": "synthetic"
                }
              },
              "mode": "logsdb",
              "number_of_replicas": "0",
              "number_of_shards": "2"
            }
          }
        }
      },
      "name": "bench-logs-otel.logsdb-bench"
    }
  ]
}
```
</details>

### Settings set by the benchmark (user-set, from `_settings`)

<details><summary>JSON</summary>

```json
{
  ".ds-logs-otel.logsdb-bench-2026.10.22-000001": {
    "settings": {
      "index": {
        "creation_date": "1792673929834",
        "hidden": "true",
        "logsdb": {
          "add_host_name_field": "true",
          "sort_on_host_name": "true"
        },
        "mapping": {
          "source": {
            "mode": "synthetic"
          }
        },
        "mode": "logsdb",
        "number_of_replicas": "0",
        "number_of_shards": "2",
        "provided_name": ".ds-logs-otel.logsdb-bench-2026.10.22-000001",
        "routing": {
          "allocation": {
            "include": {
              "_tier_preference": "data_hot"
            }
          }
        },
        "uuid": "xjpYBhupT3erb-OE38ancQ",
        "version": {
          "created": "9111000"
        }
      }
    }
  }
}
```
</details>

### Effective settings (with defaults that apply)

<details><summary>JSON</summary>

```json
{
  ".ds-logs-otel.logsdb-bench-2026.10.22-000001": {
    "defaults": {
      "index": {
        "codec": "best_compression",
        "look_back_time": "2h",
        "routing_path": [],
        "sort": {
          "field": [
            "host.name",
            "@timestamp"
          ],
          "missing": [
            "_last",
            "_last"
          ],
          "mode": [
            "min",
            "max"
          ],
          "order": [
            "asc",
            "desc"
          ]
        }
      }
    },
    "settings": {
      "index": {
        "mapping": {
          "source": {
            "mode": "synthetic"
          }
        },
        "mode": "logsdb",
        "number_of_shards": "2"
      }
    }
  }
}
```
</details>

### Mapping

<details><summary>JSON</summary>

```json
{
  ".ds-logs-otel.logsdb-bench-2026.10.22-000001": {
    "mappings": {
      "_data_stream_timestamp": {
        "enabled": true
      },
      "dynamic": "strict",
      "properties": {
        "@timestamp": {
          "ignore_malformed": false,
          "type": "date"
        },
        "attributes": {
          "properties": {
            "app": {
              "properties": {
                "cart": {
                  "properties": {
                    "items": {
                      "type": "integer"
                    }
                  }
                },
                "order": {
                  "properties": {
                    "id": {
                      "type": "keyword"
                    }
                  }
                }
              }
            },
            "exception": {
              "properties": {
                "message": {
                  "type": "match_only_text"
                },
                "type": {
                  "type": "keyword"
                }
              }
            },
            "http": {
              "properties": {
                "request": {
                  "properties": {
                    "method": {
                      "type": "keyword"
                    }
                  }
                },
                "response": {
                  "properties": {
                    "status_code": {
                      "type": "long"
                    }
                  }
                }
              }
            },
            "thread": {
              "properties": {
                "name": {
                  "type": "keyword"
                }
              }
            },
            "url": {
              "properties": {
                "path": {
                  "type": "keyword"
                }
              }
            }
          }
        },
        "body": {
          "properties": {
            "text": {
              "type": "match_only_text"
            }
          }
        },
        "host": {
          "properties": {
            "name": {
              "ignore_above": 1024,
              "type": "keyword"
            }
          }
        },
        "observed_timestamp": {
          "type": "date"
        },
        "resource": {
          "properties": {
            "attributes": {
              "properties": {
                "cloud": {
                  "properties": {
                    "region": {
                      "type": "keyword"
                    }
                  }
                },
                "deployment": {
                  "properties": {
                    "environment": {
                      "properties": {
                        "name": {
                          "type": "keyword"
                        }
                      }
                    }
                  }
                },
                "host": {
                  "properties": {
                    "name": {
                      "type": "keyword"
                    }
                  }
                },
                "k8s": {
                  "properties": {
                    "namespace": {
                      "properties": {
                        "name": {
                          "type": "keyword"
                        }
                      }
                    },
                    "pod": {
                      "properties": {
                        "name": {
                          "type": "keyword"
                        }
                      }
                    }
                  }
                },
                "service": {
                  "properties": {
                    "name": {
                      "type": "keyword"
                    },
                    "version": {
                      "type": "keyword"
                    }
                  }
                }
              }
            }
          }
        },
        "scope": {
          "properties": {
            "name": {
              "type": "keyword"
            },
            "version": {
              "type": "keyword"
            }
          }
        },
        "severity_number": {
          "type": "integer"
        },
        "severity_text": {
          "type": "keyword"
        },
        "span_id": {
          "type": "keyword"
        },
        "trace_id": {
          "type": "keyword"
        }
      }
    }
  }
}
```
</details>

## `logs-otel.columnar-bench`

### Index template (`bench-logs-otel.columnar-bench`)

<details><summary>JSON</summary>

```json
{
  "index_templates": [
    {
      "index_template": {
        "_meta": {
          "benchmark": "otel-es-benchmark",
          "signal": "logs"
        },
        "composed_of": [],
        "created_date_millis": 1792673929604,
        "data_stream": {
          "allow_custom_routing": false,
          "hidden": false
        },
        "index_patterns": [
          "logs-otel.columnar-bench"
        ],
        "modified_date_millis": 1792673929604,
        "priority": 500,
        "template": {
          "mappings": {
            "dynamic": "strict",
            "properties": {
              "@timestamp": {
                "type": "date"
              },
              "attributes": {
                "properties": {
                  "app.cart.items": {
                    "type": "integer"
                  },
                  "app.order.id": {
                    "type": "keyword"
                  },
                  "exception.message": {
                    "type": "match_only_text"
                  },
                  "exception.type": {
                    "type": "keyword"
                  },
                  "http.request.method": {
                    "type": "keyword"
                  },
                  "http.response.status_code": {
                    "type": "long"
                  },
                  "thread.name": {
                    "type": "keyword"
                  },
                  "url.path": {
                    "type": "keyword"
                  }
                }
              },
              "body": {
                "properties": {
                  "text": {
                    "type": "match_only_text"
                  }
                }
              },
              "observed_timestamp": {
                "type": "date"
              },
              "resource": {
                "properties": {
                  "attributes": {
                    "properties": {
                      "cloud.region": {
                        "type": "keyword"
                      },
                      "deployment.environment.name": {
                        "type": "keyword"
                      },
                      "host.name": {
                        "type": "keyword"
                      },
                      "k8s.namespace.name": {
                        "type": "keyword"
                      },
                      "k8s.pod.name": {
                        "type": "keyword"
                      },
                      "service.name": {
                        "type": "keyword"
                      },
                      "service.version": {
                        "type": "keyword"
                      }
                    }
                  }
                }
              },
              "scope": {
                "properties": {
                  "name": {
                    "type": "keyword"
                  },
                  "version": {
                    "type": "keyword"
                  }
                }
              },
              "severity_number": {
                "type": "integer"
              },
              "severity_text": {
                "type": "keyword"
              },
              "span_id": {
                "type": "keyword"
              },
              "trace_id": {
                "type": "keyword"
              }
            }
          },
          "settings": {
            "index": {
              "mapping": {
                "source": {
                  "mode": "synthetic"
                }
              },
              "mode": "logsdb_columnar",
              "number_of_replicas": "0",
              "number_of_shards": "2"
            }
          }
        }
      },
      "name": "bench-logs-otel.columnar-bench"
    }
  ]
}
```
</details>

### Settings set by the benchmark (user-set, from `_settings`)

<details><summary>JSON</summary>

```json
{
  ".ds-logs-otel.columnar-bench-2026.10.22-000001": {
    "settings": {
      "index": {
        "creation_date": "1792673929905",
        "hidden": "true",
        "logsdb": {
          "add_host_name_field": "true",
          "sort_on_host_name": "true"
        },
        "mapping": {
          "source": {
            "mode": "synthetic"
          }
        },
        "mode": "logsdb_columnar",
        "number_of_replicas": "0",
        "number_of_shards": "2",
        "provided_name": ".ds-logs-otel.columnar-bench-2026.10.22-000001",
        "routing": {
          "allocation": {
            "include": {
              "_tier_preference": "data_hot"
            }
          }
        },
        "uuid": "VHaj-Pc-Ro6tNB_x725v9Q",
        "version": {
          "created": "9111000"
        }
      }
    }
  }
}
```
</details>

### Effective settings (with defaults that apply)

<details><summary>JSON</summary>

```json
{
  ".ds-logs-otel.columnar-bench-2026.10.22-000001": {
    "defaults": {
      "index": {
        "codec": "best_compression",
        "look_back_time": "2h",
        "routing_path": [],
        "sort": {
          "field": [
            "host.name",
            "@timestamp"
          ],
          "missing": [
            "_last",
            "_last"
          ],
          "mode": [
            "min",
            "max"
          ],
          "order": [
            "asc",
            "desc"
          ]
        }
      }
    },
    "settings": {
      "index": {
        "mapping": {
          "source": {
            "mode": "synthetic"
          }
        },
        "mode": "logsdb_columnar",
        "number_of_shards": "2"
      }
    }
  }
}
```
</details>

### Mapping

<details><summary>JSON</summary>

```json
{
  ".ds-logs-otel.columnar-bench-2026.10.22-000001": {
    "mappings": {
      "_data_stream_timestamp": {
        "enabled": true
      },
      "dynamic": "strict",
      "properties": {
        "@timestamp": {
          "ignore_malformed": false,
          "type": "date"
        },
        "attributes.app.cart.items": {
          "type": "integer"
        },
        "attributes.app.order.id": {
          "type": "keyword"
        },
        "attributes.exception.message": {
          "type": "match_only_text"
        },
        "attributes.exception.type": {
          "type": "keyword"
        },
        "attributes.http.request.method": {
          "type": "keyword"
        },
        "attributes.http.response.status_code": {
          "type": "long"
        },
        "attributes.thread.name": {
          "type": "keyword"
        },
        "attributes.url.path": {
          "type": "keyword"
        },
        "body.text": {
          "type": "match_only_text"
        },
        "host.name": {
          "ignore_above": 1024,
          "type": "keyword"
        },
        "observed_timestamp": {
          "type": "date"
        },
        "resource.attributes.cloud.region": {
          "type": "keyword"
        },
        "resource.attributes.deployment.environment.name": {
          "type": "keyword"
        },
        "resource.attributes.host.name": {
          "type": "keyword"
        },
        "resource.attributes.k8s.namespace.name": {
          "type": "keyword"
        },
        "resource.attributes.k8s.pod.name": {
          "type": "keyword"
        },
        "resource.attributes.service.name": {
          "type": "keyword"
        },
        "resource.attributes.service.version": {
          "type": "keyword"
        },
        "scope.name": {
          "type": "keyword"
        },
        "scope.version": {
          "type": "keyword"
        },
        "severity_number": {
          "type": "integer"
        },
        "severity_text": {
          "type": "keyword"
        },
        "span_id": {
          "type": "keyword"
        },
        "trace_id": {
          "type": "keyword"
        }
      }
    }
  }
}
```
</details>

## `traces-otel.logsdb-bench`

### Index template (`bench-traces-otel.logsdb-bench`)

<details><summary>JSON</summary>

```json
{
  "index_templates": [
    {
      "index_template": {
        "_meta": {
          "benchmark": "otel-es-benchmark",
          "signal": "traces"
        },
        "composed_of": [],
        "created_date_millis": 1792673929672,
        "data_stream": {
          "allow_custom_routing": false,
          "hidden": false
        },
        "index_patterns": [
          "traces-otel.logsdb-bench"
        ],
        "modified_date_millis": 1792673929672,
        "priority": 500,
        "template": {
          "mappings": {
            "dynamic": "strict",
            "properties": {
              "@timestamp": {
                "type": "date"
              },
              "attributes": {
                "properties": {
                  "db.system": {
                    "type": "keyword"
                  },
                  "exception.message": {
                    "type": "match_only_text"
                  },
                  "exception.type": {
                    "type": "keyword"
                  },
                  "http.request.method": {
                    "type": "keyword"
                  },
                  "http.response.status_code": {
                    "type": "long"
                  },
                  "http.route": {
                    "type": "keyword"
                  },
                  "server.address": {
                    "type": "keyword"
                  }
                }
              },
              "duration": {
                "type": "long"
              },
              "kind": {
                "type": "keyword"
              },
              "name": {
                "type": "keyword"
              },
              "parent_span_id": {
                "type": "keyword"
              },
              "resource": {
                "properties": {
                  "attributes": {
                    "properties": {
                      "cloud.region": {
                        "type": "keyword"
                      },
                      "deployment.environment.name": {
                        "type": "keyword"
                      },
                      "host.name": {
                        "type": "keyword"
                      },
                      "k8s.namespace.name": {
                        "type": "keyword"
                      },
                      "k8s.pod.name": {
                        "type": "keyword"
                      },
                      "service.name": {
                        "type": "keyword"
                      },
                      "service.version": {
                        "type": "keyword"
                      }
                    }
                  }
                }
              },
              "scope": {
                "properties": {
                  "name": {
                    "type": "keyword"
                  },
                  "version": {
                    "type": "keyword"
                  }
                }
              },
              "span_id": {
                "type": "keyword"
              },
              "status": {
                "properties": {
                  "code": {
                    "type": "keyword"
                  },
                  "message": {
                    "type": "match_only_text"
                  }
                }
              },
              "trace_id": {
                "type": "keyword"
              }
            }
          },
          "settings": {
            "index": {
              "mapping": {
                "source": {
                  "mode": "synthetic"
                }
              },
              "mode": "logsdb",
              "number_of_replicas": "0",
              "number_of_shards": "2"
            }
          }
        }
      },
      "name": "bench-traces-otel.logsdb-bench"
    }
  ]
}
```
</details>

### Settings set by the benchmark (user-set, from `_settings`)

<details><summary>JSON</summary>

```json
{
  ".ds-traces-otel.logsdb-bench-2026.10.22-000001": {
    "settings": {
      "index": {
        "creation_date": "1792673929972",
        "hidden": "true",
        "logsdb": {
          "add_host_name_field": "true",
          "sort_on_host_name": "true"
        },
        "mapping": {
          "source": {
            "mode": "synthetic"
          }
        },
        "mode": "logsdb",
        "number_of_replicas": "0",
        "number_of_shards": "2",
        "provided_name": ".ds-traces-otel.logsdb-bench-2026.10.22-000001",
        "routing": {
          "allocation": {
            "include": {
              "_tier_preference": "data_hot"
            }
          }
        },
        "uuid": "ocscBlDDQz2OoV8RtRwdhA",
        "version": {
          "created": "9111000"
        }
      }
    }
  }
}
```
</details>

### Effective settings (with defaults that apply)

<details><summary>JSON</summary>

```json
{
  ".ds-traces-otel.logsdb-bench-2026.10.22-000001": {
    "defaults": {
      "index": {
        "codec": "best_compression",
        "look_back_time": "2h",
        "routing_path": [],
        "sort": {
          "field": [
            "host.name",
            "@timestamp"
          ],
          "missing": [
            "_last",
            "_last"
          ],
          "mode": [
            "min",
            "max"
          ],
          "order": [
            "asc",
            "desc"
          ]
        }
      }
    },
    "settings": {
      "index": {
        "mapping": {
          "source": {
            "mode": "synthetic"
          }
        },
        "mode": "logsdb",
        "number_of_shards": "2"
      }
    }
  }
}
```
</details>

### Mapping

<details><summary>JSON</summary>

```json
{
  ".ds-traces-otel.logsdb-bench-2026.10.22-000001": {
    "mappings": {
      "_data_stream_timestamp": {
        "enabled": true
      },
      "dynamic": "strict",
      "properties": {
        "@timestamp": {
          "ignore_malformed": false,
          "type": "date"
        },
        "attributes": {
          "properties": {
            "db": {
              "properties": {
                "system": {
                  "type": "keyword"
                }
              }
            },
            "exception": {
              "properties": {
                "message": {
                  "type": "match_only_text"
                },
                "type": {
                  "type": "keyword"
                }
              }
            },
            "http": {
              "properties": {
                "request": {
                  "properties": {
                    "method": {
                      "type": "keyword"
                    }
                  }
                },
                "response": {
                  "properties": {
                    "status_code": {
                      "type": "long"
                    }
                  }
                },
                "route": {
                  "type": "keyword"
                }
              }
            },
            "server": {
              "properties": {
                "address": {
                  "type": "keyword"
                }
              }
            }
          }
        },
        "duration": {
          "type": "long"
        },
        "host": {
          "properties": {
            "name": {
              "ignore_above": 1024,
              "type": "keyword"
            }
          }
        },
        "kind": {
          "type": "keyword"
        },
        "name": {
          "type": "keyword"
        },
        "parent_span_id": {
          "type": "keyword"
        },
        "resource": {
          "properties": {
            "attributes": {
              "properties": {
                "cloud": {
                  "properties": {
                    "region": {
                      "type": "keyword"
                    }
                  }
                },
                "deployment": {
                  "properties": {
                    "environment": {
                      "properties": {
                        "name": {
                          "type": "keyword"
                        }
                      }
                    }
                  }
                },
                "host": {
                  "properties": {
                    "name": {
                      "type": "keyword"
                    }
                  }
                },
                "k8s": {
                  "properties": {
                    "namespace": {
                      "properties": {
                        "name": {
                          "type": "keyword"
                        }
                      }
                    },
                    "pod": {
                      "properties": {
                        "name": {
                          "type": "keyword"
                        }
                      }
                    }
                  }
                },
                "service": {
                  "properties": {
                    "name": {
                      "type": "keyword"
                    },
                    "version": {
                      "type": "keyword"
                    }
                  }
                }
              }
            }
          }
        },
        "scope": {
          "properties": {
            "name": {
              "type": "keyword"
            },
            "version": {
              "type": "keyword"
            }
          }
        },
        "span_id": {
          "type": "keyword"
        },
        "status": {
          "properties": {
            "code": {
              "type": "keyword"
            },
            "message": {
              "type": "match_only_text"
            }
          }
        },
        "trace_id": {
          "type": "keyword"
        }
      }
    }
  }
}
```
</details>

## `traces-otel.columnar-bench`

### Index template (`bench-traces-otel.columnar-bench`)

<details><summary>JSON</summary>

```json
{
  "index_templates": [
    {
      "index_template": {
        "_meta": {
          "benchmark": "otel-es-benchmark",
          "signal": "traces"
        },
        "composed_of": [],
        "created_date_millis": 1792673929744,
        "data_stream": {
          "allow_custom_routing": false,
          "hidden": false
        },
        "index_patterns": [
          "traces-otel.columnar-bench"
        ],
        "modified_date_millis": 1792673929744,
        "priority": 500,
        "template": {
          "mappings": {
            "dynamic": "strict",
            "properties": {
              "@timestamp": {
                "type": "date"
              },
              "attributes": {
                "properties": {
                  "db.system": {
                    "type": "keyword"
                  },
                  "exception.message": {
                    "type": "match_only_text"
                  },
                  "exception.type": {
                    "type": "keyword"
                  },
                  "http.request.method": {
                    "type": "keyword"
                  },
                  "http.response.status_code": {
                    "type": "long"
                  },
                  "http.route": {
                    "type": "keyword"
                  },
                  "server.address": {
                    "type": "keyword"
                  }
                }
              },
              "duration": {
                "type": "long"
              },
              "kind": {
                "type": "keyword"
              },
              "name": {
                "type": "keyword"
              },
              "parent_span_id": {
                "type": "keyword"
              },
              "resource": {
                "properties": {
                  "attributes": {
                    "properties": {
                      "cloud.region": {
                        "type": "keyword"
                      },
                      "deployment.environment.name": {
                        "type": "keyword"
                      },
                      "host.name": {
                        "type": "keyword"
                      },
                      "k8s.namespace.name": {
                        "type": "keyword"
                      },
                      "k8s.pod.name": {
                        "type": "keyword"
                      },
                      "service.name": {
                        "type": "keyword"
                      },
                      "service.version": {
                        "type": "keyword"
                      }
                    }
                  }
                }
              },
              "scope": {
                "properties": {
                  "name": {
                    "type": "keyword"
                  },
                  "version": {
                    "type": "keyword"
                  }
                }
              },
              "span_id": {
                "type": "keyword"
              },
              "status": {
                "properties": {
                  "code": {
                    "type": "keyword"
                  },
                  "message": {
                    "type": "match_only_text"
                  }
                }
              },
              "trace_id": {
                "type": "keyword"
              }
            }
          },
          "settings": {
            "index": {
              "mapping": {
                "source": {
                  "mode": "synthetic"
                }
              },
              "mode": "logsdb_columnar",
              "number_of_replicas": "0",
              "number_of_shards": "2"
            }
          }
        }
      },
      "name": "bench-traces-otel.columnar-bench"
    }
  ]
}
```
</details>

### Settings set by the benchmark (user-set, from `_settings`)

<details><summary>JSON</summary>

```json
{
  ".ds-traces-otel.columnar-bench-2026.10.22-000001": {
    "settings": {
      "index": {
        "creation_date": "1792673930055",
        "hidden": "true",
        "logsdb": {
          "add_host_name_field": "true",
          "sort_on_host_name": "true"
        },
        "mapping": {
          "source": {
            "mode": "synthetic"
          }
        },
        "mode": "logsdb_columnar",
        "number_of_replicas": "0",
        "number_of_shards": "2",
        "provided_name": ".ds-traces-otel.columnar-bench-2026.10.22-000001",
        "routing": {
          "allocation": {
            "include": {
              "_tier_preference": "data_hot"
            }
          }
        },
        "uuid": "6VgTuqx_QT20ZPYOB6A8kQ",
        "version": {
          "created": "9111000"
        }
      }
    }
  }
}
```
</details>

### Effective settings (with defaults that apply)

<details><summary>JSON</summary>

```json
{
  ".ds-traces-otel.columnar-bench-2026.10.22-000001": {
    "defaults": {
      "index": {
        "codec": "best_compression",
        "look_back_time": "2h",
        "routing_path": [],
        "sort": {
          "field": [
            "host.name",
            "@timestamp"
          ],
          "missing": [
            "_last",
            "_last"
          ],
          "mode": [
            "min",
            "max"
          ],
          "order": [
            "asc",
            "desc"
          ]
        }
      }
    },
    "settings": {
      "index": {
        "mapping": {
          "source": {
            "mode": "synthetic"
          }
        },
        "mode": "logsdb_columnar",
        "number_of_shards": "2"
      }
    }
  }
}
```
</details>

### Mapping

<details><summary>JSON</summary>

```json
{
  ".ds-traces-otel.columnar-bench-2026.10.22-000001": {
    "mappings": {
      "_data_stream_timestamp": {
        "enabled": true
      },
      "dynamic": "strict",
      "properties": {
        "@timestamp": {
          "ignore_malformed": false,
          "type": "date"
        },
        "attributes.db.system": {
          "type": "keyword"
        },
        "attributes.exception.message": {
          "type": "match_only_text"
        },
        "attributes.exception.type": {
          "type": "keyword"
        },
        "attributes.http.request.method": {
          "type": "keyword"
        },
        "attributes.http.response.status_code": {
          "type": "long"
        },
        "attributes.http.route": {
          "type": "keyword"
        },
        "attributes.server.address": {
          "type": "keyword"
        },
        "duration": {
          "type": "long"
        },
        "host.name": {
          "ignore_above": 1024,
          "type": "keyword"
        },
        "kind": {
          "type": "keyword"
        },
        "name": {
          "type": "keyword"
        },
        "parent_span_id": {
          "type": "keyword"
        },
        "resource.attributes.cloud.region": {
          "type": "keyword"
        },
        "resource.attributes.deployment.environment.name": {
          "type": "keyword"
        },
        "resource.attributes.host.name": {
          "type": "keyword"
        },
        "resource.attributes.k8s.namespace.name": {
          "type": "keyword"
        },
        "resource.attributes.k8s.pod.name": {
          "type": "keyword"
        },
        "resource.attributes.service.name": {
          "type": "keyword"
        },
        "resource.attributes.service.version": {
          "type": "keyword"
        },
        "scope.name": {
          "type": "keyword"
        },
        "scope.version": {
          "type": "keyword"
        },
        "span_id": {
          "type": "keyword"
        },
        "status.code": {
          "type": "keyword"
        },
        "status.message": {
          "type": "match_only_text"
        },
        "trace_id": {
          "type": "keyword"
        }
      }
    }
  }
}
```
</details>

## `metrics-otel.tsds-bench`

### Index template (`bench-metrics-otel.tsds-bench`)

<details><summary>JSON</summary>

```json
{
  "index_templates": [
    {
      "index_template": {
        "_meta": {
          "benchmark": "otel-es-benchmark",
          "signal": "metrics"
        },
        "composed_of": [],
        "created_date_millis": 1792673929806,
        "data_stream": {
          "allow_custom_routing": false,
          "hidden": false
        },
        "index_patterns": [
          "metrics-otel.tsds-bench"
        ],
        "modified_date_millis": 1792673929806,
        "priority": 500,
        "template": {
          "mappings": {
            "dynamic": "strict",
            "properties": {
              "@timestamp": {
                "type": "date"
              },
              "attributes": {
                "properties": {
                  "stream": {
                    "time_series_dimension": true,
                    "type": "keyword"
                  }
                }
              },
              "metrics": {
                "properties": {
                  "http": {
                    "properties": {
                      "server": {
                        "properties": {
                          "duration": {
                            "properties": {
                              "p95": {
                                "time_series_metric": "gauge",
                                "type": "double"
                              }
                            }
                          },
                          "request": {
                            "properties": {
                              "count": {
                                "time_series_metric": "counter",
                                "type": "long"
                              }
                            }
                          }
                        }
                      }
                    }
                  },
                  "system": {
                    "properties": {
                      "cpu": {
                        "properties": {
                          "utilization": {
                            "time_series_metric": "gauge",
                            "type": "double"
                          }
                        }
                      },
                      "disk": {
                        "properties": {
                          "io": {
                            "properties": {
                              "read": {
                                "time_series_metric": "counter",
                                "type": "long"
                              }
                            }
                          }
                        }
                      },
                      "memory": {
                        "properties": {
                          "usage": {
                            "time_series_metric": "gauge",
                            "type": "long"
                          }
                        }
                      },
                      "network": {
                        "properties": {
                          "io": {
                            "properties": {
                              "receive": {
                                "time_series_metric": "counter",
                                "type": "long"
                              },
                              "transmit": {
                                "time_series_metric": "counter",
                                "type": "long"
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              },
              "resource": {
                "properties": {
                  "attributes": {
                    "properties": {
                      "cloud.region": {
                        "time_series_dimension": true,
                        "type": "keyword"
                      },
                      "deployment.environment.name": {
                        "type": "keyword"
                      },
                      "host.name": {
                        "time_series_dimension": true,
                        "type": "keyword"
                      },
                      "k8s.namespace.name": {
                        "time_series_dimension": true,
                        "type": "keyword"
                      },
                      "k8s.pod.name": {
                        "time_series_dimension": true,
                        "type": "keyword"
                      },
                      "service.name": {
                        "time_series_dimension": true,
                        "type": "keyword"
                      },
                      "service.version": {
                        "type": "keyword"
                      }
                    }
                  }
                }
              }
            }
          },
          "settings": {
            "index": {
              "look_back_time": "7d",
              "mapping": {
                "source": {
                  "mode": "synthetic"
                }
              },
              "mode": "time_series",
              "number_of_replicas": "0",
              "number_of_shards": "2",
              "routing_path": [
                "resource.attributes.service.name",
                "resource.attributes.host.name",
                "resource.attributes.k8s.pod.name",
                "resource.attributes.k8s.namespace.name",
                "resource.attributes.cloud.region",
                "attributes.stream"
              ]
            }
          }
        }
      },
      "name": "bench-metrics-otel.tsds-bench"
    }
  ]
}
```
</details>

### Settings set by the benchmark (user-set, from `_settings`)

<details><summary>JSON</summary>

```json
{
  ".ds-metrics-otel.tsds-bench-2026.10.22-000001": {
    "settings": {
      "index": {
        "creation_date": "1792673930126",
        "disable_sequence_numbers": "true",
        "hidden": "true",
        "look_back_time": "7d",
        "mapping": {
          "source": {
            "mode": "synthetic"
          },
          "synthetic_id": "true"
        },
        "mode": "time_series",
        "number_of_replicas": "0",
        "number_of_shards": "2",
        "provided_name": ".ds-metrics-otel.tsds-bench-2026.10.22-000001",
        "routing": {
          "allocation": {
            "include": {
              "_tier_preference": "data_hot"
            }
          }
        },
        "routing_path": [
          "resource.attributes.service.name",
          "resource.attributes.host.name",
          "resource.attributes.k8s.pod.name",
          "resource.attributes.k8s.namespace.name",
          "resource.attributes.cloud.region",
          "attributes.stream"
        ],
        "time_series": {
          "end_time": "2026-10-23T07:58:37.000Z",
          "start_time": "2026-10-15T12:58:50.000Z"
        },
        "uuid": "8rlykzxJQayquokQ6szeww",
        "version": {
          "created": "9111000"
        }
      }
    }
  }
}
```
</details>

### Effective settings (with defaults that apply)

<details><summary>JSON</summary>

```json
{
  ".ds-metrics-otel.tsds-bench-2026.10.22-000001": {
    "defaults": {
      "index": {
        "codec": "default",
        "sort": {
          "field": [
            "_tsid",
            "@timestamp"
          ],
          "missing": [
            "_last",
            "_last"
          ],
          "mode": [
            "min",
            "max"
          ],
          "order": [
            "asc",
            "desc"
          ]
        }
      }
    },
    "settings": {
      "index": {
        "look_back_time": "7d",
        "mapping": {
          "source": {
            "mode": "synthetic"
          }
        },
        "mode": "time_series",
        "number_of_shards": "2",
        "routing_path": [
          "resource.attributes.service.name",
          "resource.attributes.host.name",
          "resource.attributes.k8s.pod.name",
          "resource.attributes.k8s.namespace.name",
          "resource.attributes.cloud.region",
          "attributes.stream"
        ]
      }
    }
  }
}
```
</details>

### Mapping

<details><summary>JSON</summary>

```json
{
  ".ds-metrics-otel.tsds-bench-2026.10.22-000001": {
    "mappings": {
      "_data_stream_timestamp": {
        "enabled": true
      },
      "dynamic": "strict",
      "properties": {
        "@timestamp": {
          "type": "date"
        },
        "attributes": {
          "properties": {
            "stream": {
              "time_series_dimension": true,
              "type": "keyword"
            }
          }
        },
        "metrics": {
          "properties": {
            "http": {
              "properties": {
                "server": {
                  "properties": {
                    "duration": {
                      "properties": {
                        "p95": {
                          "time_series_metric": "gauge",
                          "type": "double"
                        }
                      }
                    },
                    "request": {
                      "properties": {
                        "count": {
                          "time_series_metric": "counter",
                          "type": "long"
                        }
                      }
                    }
                  }
                }
              }
            },
            "system": {
              "properties": {
                "cpu": {
                  "properties": {
                    "utilization": {
                      "time_series_metric": "gauge",
                      "type": "double"
                    }
                  }
                },
                "disk": {
                  "properties": {
                    "io": {
                      "properties": {
                        "read": {
                          "time_series_metric": "counter",
                          "type": "long"
                        }
                      }
                    }
                  }
                },
                "memory": {
                  "properties": {
                    "usage": {
                      "time_series_metric": "gauge",
                      "type": "long"
                    }
                  }
                },
                "network": {
                  "properties": {
                    "io": {
                      "properties": {
                        "receive": {
                          "time_series_metric": "counter",
                          "type": "long"
                        },
                        "transmit": {
                          "time_series_metric": "counter",
                          "type": "long"
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        },
        "resource": {
          "properties": {
            "attributes": {
              "properties": {
                "cloud": {
                  "properties": {
                    "region": {
                      "time_series_dimension": true,
                      "type": "keyword"
                    }
                  }
                },
                "deployment": {
                  "properties": {
                    "environment": {
                      "properties": {
                        "name": {
                          "type": "keyword"
                        }
                      }
                    }
                  }
                },
                "host": {
                  "properties": {
                    "name": {
                      "time_series_dimension": true,
                      "type": "keyword"
                    }
                  }
                },
                "k8s": {
                  "properties": {
                    "namespace": {
                      "properties": {
                        "name": {
                          "time_series_dimension": true,
                          "type": "keyword"
                        }
                      }
                    },
                    "pod": {
                      "properties": {
                        "name": {
                          "time_series_dimension": true,
                          "type": "keyword"
                        }
                      }
                    }
                  }
                },
                "service": {
                  "properties": {
                    "name": {
                      "time_series_dimension": true,
                      "type": "keyword"
                    },
                    "version": {
                      "type": "keyword"
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```
</details>

