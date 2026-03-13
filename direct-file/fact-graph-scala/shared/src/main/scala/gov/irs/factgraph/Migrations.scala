package gov.irs.factgraph
import gov.irs.factgraph.persisters.TypeContainer
import gov.irs.factgraph.types.WritableType
import ujson.{Obj, Str, Value}
import upickle.default.{read, write}

// When we make changes to the Fact Graph or Fact Dictionary, those changes not only get deployed to
// our backend servers, they get deployed to the users' browsers as well.
//
// In order to safely make changes to the Fact Graph, we can define programmatic changes that modify
// existing Fact Graphs. That way in-progress Fact Graphs (which live in the user's browser) can be
// modified to fit the new requirements, before we attempt to load them in.
object Migrations {
  val MigrationsFieldName = "/meta/migrationsApplied";

  // For each new migration, make a function for it, then add it to this list
  // Migrations numbers should increase monotonically, i.e. m0_, m1_, m2_, ...
  // It's very important that these migrations stay in order, so don't re-order the list.
  // The leading number (i.e. m1) is a way of explicitly denoting that order, but it's the List
  // order itself that matters for ensuring consistency.
  private val AllMigrations = List(
    m1_BlankMigration,
    m2_DeleteInvalidAddresses,
    m3_NormalizeLegacyWrapperPayloads,
  )
  val TotalMigrations: Int = AllMigrations.length

  def run(data: Map[String, Value], numMigrations: Int): Map[Path, WritableType] =
    AllMigrations
      .drop(numMigrations) // get the missing migrations
      .foldLeft(data)((data, migration) => migration(data)) // apply each of them
      .map((k, v) => (Path(k), read[TypeContainer](v).item)) // convert the result to Map[Path, WritableType]

  // Blank migration to test the mechanism
  private def m1_BlankMigration(data: Map[String, Value]): Map[String, Value] =
    data

  // Remove addresses that don't match MeF validation
  private def m2_DeleteInvalidAddresses(data: Map[String, Value]): Map[String, Value] =
    data.filterNot((_, value) =>
      value("$type").value == "gov.irs.factgraph.persisters.AddressWrapper" &&
        !value("item")("streetAddress").str.matches("[A-Za-z0-9]( ?[A-Za-z0-9\\-/])*"),
    )

  // Normalize older Java wrapper payloads so persisted/browser facts keep loading after
  // the newer Scala readers started expecting bean-style object shapes.
  private def m3_NormalizeLegacyWrapperPayloads(data: Map[String, Value]): Map[String, Value] =
    data.map((path, value) => (path, normalizeLegacyWrapperPayload(value)))

  private def normalizeLegacyWrapperPayload(value: Value): Value =
    value.objOpt match
      case Some(wrapper) =>
        wrapper.get("$type").map(_.str) match
          case Some("gov.irs.factgraph.persisters.DayWrapper") =>
            wrapper.get("item") match
              case Some(Str(dateValue)) =>
                replaceItem(wrapper, Obj("date" -> Str(dateValue)))
              case _ => value
          case Some("gov.irs.factgraph.persisters.EinWrapper") =>
            wrapper.get("item").flatMap(_.objOpt) match
              case Some(item) if item.contains("suffix") && !item.contains("serial") =>
                val normalizedItem = Obj.from(item.value.toSeq.filterNot(_._1 == "suffix"))
                normalizedItem("serial") = item("suffix")
                replaceItem(wrapper, normalizedItem)
              case _ => value
          case _ => value
      case None => value

  private def replaceItem(wrapper: Obj, normalizedItem: Value): Value =
    val normalizedWrapper = Obj.from(wrapper.value.toSeq.filterNot(_._1 == "item"))
    normalizedWrapper("item") = normalizedItem
    normalizedWrapper

}
