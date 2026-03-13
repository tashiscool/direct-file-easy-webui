package gov.irs.factgraph.compnodes

import gov.irs.factgraph.{FactDictionary, Factual}
import gov.irs.factgraph.definitions.fact.{CompNodeConfigTrait, WritableConfigTrait}

object LegacyDateNode extends CompNodeFactory with WritableNodeFactory:
  override val Key: String = "Date"

  override def fromWritableConfig(e: WritableConfigTrait)(using Factual)(using
      FactDictionary,
  ): CompNode =
    DayNode.fromWritableConfig(e)

  override def fromDerivedConfig(e: CompNodeConfigTrait)(using Factual)(using
      FactDictionary,
  ): CompNode =
    DayNode.fromDerivedConfig(e)
