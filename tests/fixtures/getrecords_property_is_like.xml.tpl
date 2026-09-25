<?xml version="1.0" encoding="UTF-8"?>
<!-- Generated with Claude Code (https://claude.com/claude-code) -->
<csw:GetRecords xmlns:csw="http://www.opengis.net/cat/csw/2.0.2"
    xmlns:ogc="http://www.opengis.net/ogc"
    service="CSW" version="2.0.2"
    resultType="results" outputSchema="csw:IsoRecord"
    maxRecords="10">
  <csw:Query typeNames="csw:Record">
    <csw:ElementSetName>brief</csw:ElementSetName>
    <csw:Constraint version="1.1.0">
      <ogc:Filter>
        <ogc:PropertyIsLike wildCard="{wildcard}" singleChar="_" escapeChar="\">
          <ogc:PropertyName>AnyText</ogc:PropertyName>
          <ogc:Literal>{literal}</ogc:Literal>
        </ogc:PropertyIsLike>
      </ogc:Filter>
    </csw:Constraint>
  </csw:Query>
</csw:GetRecords>
