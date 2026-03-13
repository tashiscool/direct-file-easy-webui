package gov.irs.factgraph.compnodes

import gov.irs.factgraph.{FactDictionary, Factual}
import gov.irs.factgraph.definitions.fact.CompNodeConfigTrait

object Switch extends CompNodeFactory:
  override val Key: String = "Switch"

  private def getLegacyCaseNodes(
      e: CompNodeConfigTrait,
  )(using Factual)(using FactDictionary): (BooleanNode, CompNode) =
    val children = e.children.map(CompNode.fromDerivedConfig).toSeq

    children match
      case whenNode :: thenNode :: Nil =>
        whenNode match
          case booleanNode: BooleanNode =>
            (booleanNode, thenNode)
          case _ =>
            throw new UnsupportedOperationException(
              s"legacy <Case> condition must be boolean: $e",
            )
      case _ =>
        throw new IllegalArgumentException(
          s"<Case> must have a legacy condition/result pair or explicit <When>/<Then>: $e",
        )

  private def getDefaultNode(
      e: CompNodeConfigTrait,
  )(using Factual)(using FactDictionary): Option[(BooleanNode, CompNode)] =
    e.children
      .find(_.typeName == "Default")
      .map(defaultNode =>
        (
          BooleanNode.True.node,
          CompNode.getConfigChildNode(defaultNode),
        )
      )

  def apply(cases: Seq[(BooleanNode, CompNode)]): CompNode =
    val (_, thens) = cases.unzip

    try {
      thens.head.switch(cases.toList)
    } catch {
      case e: ClassCastException =>
        val thenTypes = thens.map(_.getClass.getSimpleName).mkString(", ")
        throw new UnsupportedOperationException(
          s"cannot switch between nodes of different types: $thenTypes",
        )
    }

  override def fromDerivedConfig(
      e: CompNodeConfigTrait,
  )(using Factual)(using FactDictionary): CompNode =
    try {
      val cases = for {
        c <- e.children.filter(x => x.typeName == "Case")
      } yield
        if (c.children.exists(_.typeName == "When")) {
          (
            CompNode.getConfigChildNode(c, "When").asInstanceOf[BooleanNode],
            CompNode.getConfigChildNode(c, "Then"),
          )
        } else {
          getLegacyCaseNodes(c)
        }

      val casesWithDefault = cases.toSeq ++ getDefaultNode(e).toSeq

      if (casesWithDefault.isEmpty)
        throw new IllegalArgumentException(
          s"Switch must have at least one child node: $e",
        )

      this(casesWithDefault)
    } catch {
      case exc: UnsupportedOperationException =>
        throw new UnsupportedOperationException(s"${exc.getMessage}: $e", exc)
      case e: ClassCastException =>
        throw new UnsupportedOperationException(
          s"When must be boolean: $e",
        )
    }
