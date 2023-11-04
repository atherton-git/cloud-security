#!/bin/bash
total_lines=$(cat iprange.txt | wc -l)
lines_no=0
echo "["
while read -r line; do
  lines_no=$(( $lines_no + 1 ))
  echo " {"
  echo "  \"source\": \"${line}\","
  echo "  \"protocol\": \"17\","
  echo "  \"isStateless\": \"false\","
  echo "  \"tcp-options\": {"
  echo "    \"destination_port_range\": {"
  echo "      \"max\": 51820,"
  echo "      \"min\": 51820"
  echo "    }"
  echo "  },"
  echo "  \"Description\": \"OCI WAF UDP Port 51820 Rules\""
  if [[ $lines_no -eq $total_lines ]]; then
    echo " }"
  else
    echo " },"
  fi
done < iprange.txt
echo "]"
